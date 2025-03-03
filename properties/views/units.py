from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from properties.models.units import Unit
from properties.serializers.units import UnitSerializer


class UnitAPIView(APIView):
    """
    API View for listing all units and
    creating a new unit with nested RoomPartition.
    """
    # permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Retrieve all units.
        """
        units = Unit.objects.all()
        serializer = UnitSerializer(units, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        """
        Create a new unit with nested RoomPartition.
        """
        serializer = UnitSerializer(data=request.data)
        if serializer.is_valid():
            unit = serializer.save()
            return Response(UnitSerializer(unit).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UnitDetailAPIView(APIView):
    """
    API View for retrieving, updating, and deleting a specific unit.
    """
    # permission_classes = [IsAuthenticated]

    def get_object(self, unit_id):
        try:
            return Unit.objects.get(id=unit_id)
        except Unit.DoesNotExist:
            return None

    def get(self, request, unit_id):
        """
        Retrieve a specific unit.
        """
        unit = self.get_object(unit_id)
        if unit is None:
            return Response(
                {"error": "Unit not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = UnitSerializer(unit)
        return Response(
            serializer.data, status=status.HTTP_200_OK
        )

    def put(self, request, unit_id):
        """
        Update an existing unit.
        """
        unit = self.get_object(unit_id)
        if unit is None:
            return Response(
                {"error": "Unit not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = UnitSerializer(unit, data=request.data)
        if serializer.is_valid():
            unit = serializer.save()
            return Response(
                UnitSerializer(unit).data,
                status=status.HTTP_200_OK
            )
        return Response(
            serializer.errors, status=status.HTTP_400_BAD_REQUEST
        )

    def patch(self, request, unit_id):
        """
        Partially update an existing unit.
        """
        unit = self.get_object(unit_id)
        if unit is None:
            return Response(
                {"error": "Unit not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = UnitSerializer(
            unit, data=request.data, partial=True
        )
        if serializer.is_valid():
            unit = serializer.save()
            return Response(
                UnitSerializer(unit).data, status=status.HTTP_200_OK
            )
        return Response(
            serializer.errors, status=status.HTTP_400_BAD_REQUEST
        )

    def delete(self, request, unit_id):
        """
        Delete an existing unit.
        """
        unit = self.get_object(unit_id)
        if unit is None:
            return Response(
                {"error": "Unit not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        unit.delete()
        return Response(
            {"message": "Unit deleted successfully"},
            status=status.HTTP_204_NO_CONTENT
        )
