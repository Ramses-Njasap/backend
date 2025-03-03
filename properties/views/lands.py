from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from django.shortcuts import get_object_or_404
from properties.models.lands import LandProperty
from properties.serializers.lands import LandPropertySerializer
from properties.models.environments import Environment


class LandPropertyAPIView(APIView):
    """Handles listing all land properties and creating a new one"""

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """List all land properties"""
        land_properties = LandProperty.objects.all()
        serializer = LandPropertySerializer(land_properties, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        """Create a new land property"""
        serializer = LandPropertySerializer(data=request.data)
        if serializer.is_valid():
            environment_id = request.data.get("environment")
            environment = get_object_or_404(Environment, id=environment_id)

            # Ensure the environment is not already linked
            if LandProperty.objects.filter(environment=environment).exists():
                return Response(
                    {
                        "error": (
                            "This environment is already "
                            "linked to a land property."
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            land_property = LandProperty.objects.create(environment=environment)
            return Response(
                LandPropertySerializer(land_property).data,
                status=status.HTTP_201_CREATED
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


class LandPropertyDetailAPIView(APIView):
    """Handles retrieving, updating, and deleting a specific land property"""

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_object(self, pk):
        """Helper method to get the LandProperty instance"""
        return get_object_or_404(LandProperty, pk=pk)

    def get(self, request, pk):
        """Retrieve a specific land property"""
        land_property = self.get_object(pk)
        serializer = LandPropertySerializer(land_property)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, pk):
        """Fully update a land property"""
        land_property = self.get_object(pk)
        serializer = LandPropertySerializer(
            land_property, data=request.data
        )
        if serializer.is_valid():
            serializer.save()
            return Response(
                serializer.data, status=status.HTTP_200_OK
            )
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

    def patch(self, request, pk):
        """Partially update a land property"""
        land_property = self.get_object(pk)
        serializer = LandPropertySerializer(
            land_property, data=request.data, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(
            serializer.errors, status=status.HTTP_400_BAD_REQUEST
        )

    def delete(self, request, pk):
        """Delete a land property"""
        land_property = self.get_object(pk)
        land_property.delete()
        return Response(
            {"message": "Land property deleted successfully"},
            status=status.HTTP_204_NO_CONTENT
        )
