from rest_framework import serializers
from django.contrib.gis.geos import Point, Polygon
from properties.models.buildings import Building


class BuildingSerializer(serializers.ModelSerializer):
    # Custom fields for calculated properties
    age = serializers.SerializerMethodField()
    number_of_rooms = serializers.SerializerMethodField()
    rooms_remaining = serializers.SerializerMethodField()

    class Meta:
        model = Building
        fields = [
            'id', 'uploader', 'name', 'description', 'availability',
            'number_of_shares', 'number_of_views', 'built_on', 'uploaded_on',
            'updated_at', 'geom', 'multi_units', 'units', 'distance_from_road',
            'boundary', 'general_amenities', 'partial_upload', 'query_id',
            'age', 'number_of_rooms', 'rooms_remaining'
        ]
        read_only_fields = ['id', 'uploaded_on', 'updated_at', 'query_id']

    def get_age(self, obj):
        return obj.age()

    def get_number_of_rooms(self, obj):
        return obj.number_of_rooms()

    def get_rooms_remaining(self, obj):
        return obj.rooms_remaining()

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        # Handle geospatial fields
        if instance.geom:
            representation['geom'] = {
                'type': 'Point',
                'coordinates': [instance.geom.x, instance.geom.y, instance.geom.z]
            }
        if instance.boundary:
            representation['boundary'] = {
                'type': 'Polygon',
                'coordinates': instance.boundary.coords
            }

        return representation

    def to_internal_value(self, data):
        # Handle geospatial fields during deserialization
        geom_data = data.get('geom')
        boundary_data = data.get('boundary')

        if geom_data and isinstance(geom_data, dict):
            data['geom'] = Point(
                geom_data['coordinates'][0],
                geom_data['coordinates'][1],
                geom_data['coordinates'][2]
            )

        if boundary_data and isinstance(boundary_data, dict):
            data['boundary'] = Polygon(boundary_data['coordinates'])

        return super().to_internal_value(data)
