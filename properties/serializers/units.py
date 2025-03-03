from rest_framework import serializers
from properties.models.units import Unit
from configurations.models.currencies import Currencies
from properties.serializers.rooms import RoomPartitionSerializer


class UnitSerializer(serializers.ModelSerializer):
    """Serializer for Unit with Nested RoomPartition"""

    rooms = RoomPartitionSerializer(many=True)  # Nested serializer
    currency = serializers.SlugRelatedField(
        queryset=Currencies.objects.all(), slug_field="code"
    )

    class Meta:
        model = Unit
        fields = [
            'id', 'home_type', 'name', 'number_of_rooms', 'rooms_taken', 'rooms',
            'cost', 'currency', 'exchange_rate_from_usd_upon_upload', 'query_id'
        ]

    def to_representation(self, instance):
        """Custom representation of Unit including nested RoomPartition"""
        representation = super().to_representation(instance)
        representation['rooms'] = RoomPartitionSerializer(
            instance.rooms.all(), many=True).data
        return representation

    def create(self, validated_data):
        """Create a Unit and associate it with RoomPartitions"""

        # Extract nested room data
        rooms_data = validated_data.pop('rooms', [])

        # Create Unit instance
        unit = Unit.objects.create(**validated_data)

        # Create RoomPartition instances and link them to Unit
        for room_data in rooms_data:
            room_partition_serializer = RoomPartitionSerializer(data=room_data)
            if room_partition_serializer.is_valid(raise_exception=True):
                room_partition = room_partition_serializer.save()
                unit.rooms.add(room_partition)

        return unit

    def update(self, instance, validated_data):
        """Update Unit and its related RoomPartitions"""

        rooms_data = validated_data.pop('rooms', None)

        # Update Unit instance fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Update RoomPartitions if provided
        if rooms_data is not None:
            instance.rooms.clear()  # Remove all existing RoomPartition associations
            for room_data in rooms_data:
                room_partition_serializer = RoomPartitionSerializer(data=room_data)
                if room_partition_serializer.is_valid(raise_exception=True):
                    room_partition = room_partition_serializer.save()
                    instance.rooms.add(room_partition)

        return instance
