from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from properties.models.buildings import Building
from properties.serializers.buildings import BuildingSerializer


class BuildingAPIView(APIView):
    def get(self, pk=None):
        if pk:
            try:
                building = Building.objects.get(pk=pk)
                serializer = BuildingSerializer(building)
                return Response(serializer.data)
            except Building.DoesNotExist:
                return Response(
                    {'error': 'Building not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
        else:
            buildings = Building.objects.all()
            serializer = BuildingSerializer(buildings, many=True)
            return Response(serializer.data)

    def post(self, request):
        serializer = BuildingSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk):
        try:
            building = Building.objects.get(pk=pk)
        except Building.DoesNotExist:
            return Response(
                {'error': 'Building not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = BuildingSerializer(building, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        try:
            building = Building.objects.get(pk=pk)
        except Building.DoesNotExist:
            return Response(
                {'error': 'Building not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = BuildingSerializer(building, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        try:
            building = Building.objects.get(pk=pk)
        except Building.DoesNotExist:
            return Response(
                {'error': 'Building not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        building.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
