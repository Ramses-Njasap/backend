from rest_framework_gis.serializers import GeoFeatureModelSerializer
from rest_framework import serializers
from properties.models.environments import Environment
from properties.serializers.profiles import ProfileSerializer


class EnvironmentSerializer(GeoFeatureModelSerializer):
    """Serializer for the Environment model with GeoDjango support"""

    uploader = ProfileSerializer(read_only=True)  # Nested uploader
    availability_display = serializers.CharField(
        source="get_availability_display", read_only=True
    )  # Human-readable availability status
    uploaded_on = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)
    updated_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)

    class Meta:
        model = Environment
        geo_field = "geom"  # Primary GeoJSON geometry field
        fields = [
            "id", "uploader", "name", "description", "availability",
            "availability_display", "number_of_shares", "number_of_views",
            "uploaded_on", "updated_at", "distance_from_road", "geom", "boundary"
        ]

    def to_representation(self, instance):
        """Custom representation to format data"""
        data = super().to_representation(instance)

        # Format the geometry fields as GeoJSON
        if instance.geom:
            data["geom"] = {
                "type": "Point",
                "coordinates": instance.geom.coords
            }

        if instance.boundary:
            data["boundary"] = {
                "type": "Polygon",
                "coordinates": instance.boundary.coords
            }

        # Round distance_from_road for better readability
        if instance.distance_from_road:
            data["distance_from_road"] = round(instance.distance_from_road, 2)

        return data

    def validate_geom(self, value):
        """Ensure geom field is a valid 3D point"""
        if value and len(value.coords) != 3:
            raise serializers.ValidationError(
                "geom must be a valid 3D point (longitude, latitude, altitude)."
            )
        return value

    def create(self, validated_data):
        """Custom create method to handle additional processing"""
        return super().create(validated_data)

    def update(self, instance, validated_data):
        """Custom update method"""
        return super().update(instance, validated_data)
