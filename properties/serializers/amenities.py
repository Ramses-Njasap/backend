from rest_framework import serializers
from properties.models.amenities import Amenity


class AmenitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Amenity
        fields = '__all__'
