from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from properties.models.rooms import Partition, RoomPartition
from properties.serializers.rooms import (
    PartitionSerializer, RoomPartitionSerializer
)


class PartitionAPIView(APIView):
    """
    APIView for handling CRUD operations on Partition model.
    """

    def get(self, request):
        """Handles retrieving a list of all partitions (GET)."""
        partitions = Partition.objects.all()
        serializer = PartitionSerializer(
            partitions, many=True, context={'request': request}
        )
        return Response(
            serializer.data, status=status.HTTP_200_OK
        )

    def post(self, request):
        """Handles creating a new partition (POST)."""
        serializer = PartitionSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                serializer.data, status=status.HTTP_201_CREATED
            )
        return Response(
            serializer.errors, status=status.HTTP_400_BAD_REQUEST
        )


class PartitionDetailAPIView(APIView):
    """
    APIView for handling GET, PUT, PATCH,
    and DELETE on a single Partition.
    """

    def get_object(self, pk):
        """Retrieves the Partition object by its ID."""
        try:
            return Partition.objects.get(pk=pk)
        except Partition.DoesNotExist:
            return None

    def get(self, request, pk):
        """Handles retrieving a specific partition (GET)."""
        partition = self.get_object(pk)
        if not partition:
            return Response(
                {"error": "Partition not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        serializer = PartitionSerializer(
            partition, context={'request': request}
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, pk):
        """Handles full update of a partition (PUT)."""
        partition = self.get_object(pk)
        if not partition:
            return Response(
                {"error": "Partition not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        serializer = PartitionSerializer(partition, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                serializer.data, status=status.HTTP_200_OK
            )
        return Response(
            serializer.errors, status=status.HTTP_400_BAD_REQUEST
        )

    def patch(self, request, pk):
        """
        Handles partial update of a partition (PATCH).
        """

        partition = self.get_object(pk)
        if not partition:
            return Response(
                {"error": "Partition not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        serializer = PartitionSerializer(
            partition, data=request.data, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(
                serializer.data, status=status.HTTP_200_OK
            )
        return Response(
            serializer.errors, status=status.HTTP_400_BAD_REQUEST
        )

    def delete(self, request, pk):
        """Handles deletion of a partition (DELETE)."""
        partition = self.get_object(pk)
        if not partition:
            return Response(
                {"error": "Partition not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        partition.delete()
        return Response(
            {"message": "Partition deleted successfully"},
            status=status.HTTP_204_NO_CONTENT
        )


class RoomPartitionAPIView(APIView):
    """
    Handles RoomPartition list and creation.
    """

    def get(self, request):
        """
        Retrieves all RoomPartitions (nested Partition included).
        """
        room_partitions = RoomPartition.objects.all()
        serializer = RoomPartitionSerializer(
            room_partitions, many=True
        )
        return Response(
            serializer.data, status=status.HTTP_200_OK
        )

    def post(self, request):
        """
        Creates RoomPartition with a nested Partition.
        """

        serializer = RoomPartitionSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                serializer.data, status=status.HTTP_201_CREATED
            )
        return Response(
            serializer.errors, status=status.HTTP_400_BAD_REQUEST
        )


class RoomPartitionDetailAPIView(APIView):
    """
    Handles single RoomPartition retrieval, update, and delete.
    """

    def get_object(self, pk):
        """Fetches a RoomPartition by ID."""
        try:
            return RoomPartition.objects.get(pk=pk)
        except RoomPartition.DoesNotExist:
            return None

    def get(self, request, pk):
        """
        Retrieves a single RoomPartition with a nested Partition.
        """

        room_partition = self.get_object(pk)
        if not room_partition:
            return Response(
                {"error": "RoomPartition not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        serializer = RoomPartitionSerializer(room_partition)
        return Response(
            serializer.data, status=status.HTTP_200_OK
        )

    def put(self, request, pk):
        """
        Updates a RoomPartition along with its Partition.
        """

        room_partition = self.get_object(pk)
        if not room_partition:
            return Response(
                {"error": "RoomPartition not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        serializer = RoomPartitionSerializer(
            room_partition, data=request.data
        )
        if serializer.is_valid():
            serializer.save()
            return Response(
                serializer.data, status=status.HTTP_200_OK
            )
        return Response(
            serializer.errors, status=status.HTTP_400_BAD_REQUEST
        )

    def patch(self, request, pk):
        """
        Partially updates a RoomPartition and its Partition.
        """

        room_partition = self.get_object(pk)
        if not room_partition:
            return Response(
                {"error": "RoomPartition not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        serializer = RoomPartitionSerializer(
            room_partition, data=request.data, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(
                serializer.data, status=status.HTTP_200_OK
            )
        return Response(
            serializer.errors, status=status.HTTP_400_BAD_REQUEST
        )

    def delete(self, request, pk):
        """Deletes a RoomPartition."""
        room_partition = self.get_object(pk)
        if not room_partition:
            return Response(
                {"error": "RoomPartition not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        room_partition.delete()
        return Response(
            {"message": "RoomPartition deleted successfully"},
            status=status.HTTP_204_NO_CONTENT
        )
