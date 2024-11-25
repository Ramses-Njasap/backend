from rest_framework.serializers import ModelSerializer

from rest_framework_gis.serializers import GeoFeatureModelSerializer

from properties.models.homes import Partition, RoomPartition, Room, Home
from properties.models.amenities import Amenity

from utilities import response


class PartitionSerializer(ModelSerializer):
    class Meta:
        model = Partition
        fields = ('name', 'query_id')
        read_only_fields = (
            'name', 'query_id'
        )
        extra_kwargs = {
            'name': {'required': True},
        }
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)

        return representation
    
    def create(self, validated_data):
        name = validated_data.get('name', None)

        if name:

            try:
                partition_instance = Partition.objects.create(name=name)
                
                return partition_instance
            except Exception as e:
                response.errors(
                    field_error='An error occurred in creating room partition',
                    for_developer=str(e),
                    code="INTERNAL_SERVER_ERROR",
                    status_code=500
                )
        else:
            response.errors(
                field_error='Partition name cannot be a null value',
                for_developer='Partition name cannot be null value',
                code="BAD_REQUEST",
                status_code=400
            )


class RoomPartitionSerializer(ModelSerializer):
    class Meta:
        model = RoomPartition
        fields = ('partition', 'number', 'query_id')
        read_only_fields = ("query_id",)
        extra_kwargs = {
            'name': {'required': True},
        }

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        return representation
    
    def create(self, validated_data):

        return super().create(validated_data)


class RoomSerializer(ModelSerializer):
    ...


class HomeSerializer(GeoFeatureModelSerializer):
    class Meta:
        model = Home
        geo_field = ("geom", "boundary")
        fields = ("uploader", "name", "description", "availability", "built_on",
                  "geom", "multi_rooms", "rooms", "distance_from_road", "boundary",
                  "land_boundary", "general_amenities", "partial_upload", "query_id")
        read_only_fields = ("query_id",)
        extra_kwargs = {
            "uploader": {"required": True},
            "name": {"required": True},
            "description": {"required": False},
            "availability": {"required": False},
            "built_on": {"required": False},
            "geom": {"required": False},
            "multi_rooms": {"required": False},
            "distance_from_road": {"required": False},
            "boundary": {"required": False},
            "land_boundary": {"required": False},
            "partial_upload": {"required": False}
        }

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        return representation
    
    def create(self, validated_data):
        uploader = validated_data.get("uploader", None)
        name = validated_data.get("name", None)
        description = validated_data.get("description", None)
        availability = validated_data.get("availability", None)
        built_on = validated_data.get("built_on", None)
        geom = validated_data.get("geom", {})
        multi_rooms = validated_data.get("multi_rooms", None)
        rooms = validated_data.get("rooms", [])
        # example `rooms` = [{"home_type": "", "number_of_rooms": 5, "rooms_taken"}]
        boundary = validated_data.get("boundary", [])
        land_boundary = validated_data.get("land_boundary", {})
        general_amenities = validated_data.get("general_amenities", [])

        if not None in (uploader, name):
            # Create a dictionary of fields to be used in the Home creation
            create_fields = {
                'uploader': uploader,
                'name': name,
                'description': description if description else None,
                'availability': availability,
                'built_on': built_on if built_on else None,
                'multi_rooms': multi_rooms if multi_rooms else None,
            }

            # Remove any fields that have None or empty values
            create_fields = {key: value for key, value in create_fields.items() if value}

            try:
                # Create the Home instance using only the fields that are present
                home_instance = Home.objects.create(**create_fields)

                # Fetch the Amenity instances using the list of IDs
                general_amenities_instances = Amenity.objects.filter(id__in=general_amenities)

                home_instance.general_amenities.add(*general_amenities_instances)

                if not rooms or rooms is None:
                    home_instance.partial_upload = True

                    home_instance.save()

            except Exception as e:
                response.errors(
                    field_error="An Error Occurred .",
                    for_developer=str(e),
                    code="INTERNAL_SERVER_ERROR",
                    status_code=500
                )

            return home_instance
        
        else:

            field_error = "Cannot Identify User and/or Home must have a name" if not uploader else "Home name is empty"
            response.errors(
                field_error=field_error,
                for_developer="Check if user is authenticated or check if `name` field has a value",
                code="BAD_REQUEST",
                status_code=400
            )