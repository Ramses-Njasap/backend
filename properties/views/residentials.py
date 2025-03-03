from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from django.shortcuts import get_object_or_404
from properties.models.residentials import ResidentialProperty
from properties.serializers.residentials import ResidentialPropertySerializer


class ResidentialPropertyAPIView(APIView):
    """Handles listing all residential properties and creating a new one"""

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """List all residential properties"""
        properties = ResidentialProperty.objects.all()
        serializer = ResidentialPropertySerializer(properties, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        """Create a new residential property"""
        serializer = ResidentialPropertySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ResidentialPropertyDetailAPIView(APIView):
    """
    Handles retrieving, updating, and deleting a specific
    residential property
    """

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_object(self, pk):
        """Helper method to get the ResidentialProperty instance"""
        return get_object_or_404(ResidentialProperty, pk=pk)

    def get(self, request, pk):
        """Retrieve a specific residential property"""
        property_instance = self.get_object(pk)
        serializer = ResidentialPropertySerializer(property_instance)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, pk):
        """Fully update a residential property"""
        property_instance = self.get_object(pk)
        serializer = ResidentialPropertySerializer(property_instance, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        """Partially update a residential property"""
        property_instance = self.get_object(pk)
        serializer = ResidentialPropertySerializer(
            property_instance, data=request.data, partial=True
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
        """Delete a residential property"""
        property_instance = self.get_object(pk)
        property_instance.delete()
        return Response(
            {"message": "Residential property deleted successfully"},
            status=status.HTTP_204_NO_CONTENT
        )
