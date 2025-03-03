from rest_framework import serializers
from properties.models.buildings import Building
from properties.models.amenities import Amenity
from properties.models.environments import Environment
from properties.models.residentials import (
    ResidentialPropertyType, ResidentialPropertyTypeInclusive,
    ResidentialProperty
)

from properties.serializers.environments import EnvironmentSerializer


class ResidentialPropertyTypeSerializer(serializers.ModelSerializer):
    """Serializer for ResidentialPropertyType"""

    class Meta:
        model = ResidentialPropertyType
        fields = ['id', 'name']


class ResidentialPropertyTypeInclusiveSerializer(serializers.ModelSerializer):
    """Serializer for ResidentialPropertyTypeInclusive (nested property types)"""

    main = ResidentialPropertyTypeSerializer()
    includes = ResidentialPropertyTypeSerializer(many=True)

    class Meta:
        model = ResidentialPropertyTypeInclusive
        fields = ['id', 'main', 'includes']


class BuildingSerializer(serializers.ModelSerializer):
    """Serializer for Building model"""

    class Meta:
        model = Building
        fields = ['id', 'name', 'description']  # Customize fields as needed


class AmenitySerializer(serializers.ModelSerializer):
    """Serializer for Amenity model"""

    class Meta:
        model = Amenity
        fields = ['id', 'name', 'description']


class ResidentialPropertySerializer(serializers.ModelSerializer):
    """Serializer for ResidentialProperty with nested relationships"""

    environment = EnvironmentSerializer()
    _type = ResidentialPropertyTypeSerializer()
    buildings = BuildingSerializer(many=True)
    general_amenities = AmenitySerializer(many=True)

    class Meta:
        model = ResidentialProperty
        fields = [
            'id', 'environment', '_type', 'buildings', 'built_on',
            'general_amenities', 'partial_upload', 'query_id'
        ]

    def create(self, validated_data):
        """Custom create method to handle nested data"""

        # Extract nested data
        environment_data = validated_data.pop('environment')
        type_data = validated_data.pop('_type')
        buildings_data = validated_data.pop('buildings', [])
        amenities_data = validated_data.pop('general_amenities', [])

        # Get or create related objects
        environment, _ = Environment.objects.get_or_create(**environment_data)
        property_type, _ = ResidentialPropertyType.objects.get_or_create(**type_data)

        # Create the main ResidentialProperty object
        residential_property = ResidentialProperty.objects.create(
            environment=environment, _type=property_type, **validated_data
        )

        # Add ManyToMany relationships
        residential_property.buildings.set(buildings_data)
        residential_property.general_amenities.set(amenities_data)

        return residential_property
