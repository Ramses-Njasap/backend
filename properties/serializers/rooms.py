from rest_framework import serializers
from properties.models.rooms import Partition, RoomPartition


class PartitionSerializer(serializers.ModelSerializer):
    """Serializer for Partition model with explicitly defined methods."""

    class Meta:
        model = Partition
        fields = '__all__'  # Include all fields

    def create(self, validated_data):
        """Handles creation of a new Partition instance (POST)."""
        return Partition.objects.create(**validated_data)

    def update(self, instance, validated_data):
        """Handles updating a Partition instance (PUT)."""
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance

    def partial_update(self, instance, validated_data):
        """Handles partial update of a Partition instance (PATCH)."""
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance

    def delete(self, instance):
        """Handles deletion of a Partition instance (DELETE)."""
        instance.delete()

    def to_representation(self, instance):
        """Customizes the response data to filter out specific fields."""
        data = super().to_representation(instance)

        # Example: Exclude `query_id` from response if user is not an admin
        request = self.context.get('request')
        if request and not request.user.is_staff:
            data.pop('query_id', None)

        return data


class RoomPartitionSerializer(serializers.ModelSerializer):
    """Serializer for RoomPartition with nested Partition handling."""

    # Nest Partition inside RoomPartition
    partition = PartitionSerializer()

    class Meta:
        model = RoomPartition
        fields = '__all__'

    def create(self, validated_data):
        """Handles RoomPartition creation with nested Partition."""
        partition_data = validated_data.pop('partition')
        partition, _ = Partition.objects.get_or_create(**partition_data)
        room_partition = RoomPartition.objects.create(
            partition=partition, **validated_data
        )
        return room_partition

    def update(self, instance, validated_data):
        """Handles updating RoomPartition along with Partition."""
        partition_data = validated_data.pop('partition', None)

        # Update Partition if data is provided
        if partition_data:
            partition_serializer = PartitionSerializer(
                instance.partition, data=partition_data, partial=True
            )
            if partition_serializer.is_valid():
                partition_serializer.save()

        return super().update(instance, validated_data)
