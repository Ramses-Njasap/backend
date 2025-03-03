from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from django.shortcuts import get_object_or_404
from properties.models.environments import Environment
from properties.serializers.environments import EnvironmentSerializer


class EnvironmentAPIView(APIView):
    """Handles listing all environments and creating a new one"""

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """List all environments"""
        environments = Environment.objects.all()
        serializer = EnvironmentSerializer(environments, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        """Create a new environment"""
        serializer = EnvironmentSerializer(data=request.data)
        if serializer.is_valid():

            # Ensure uploader is the logged-in user
            serializer.save(uploader=request.user.profile)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EnvironmentDetailAPIView(APIView):
    """Handles retrieving, updating, and deleting a specific environment"""

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_object(self, pk):
        """Helper method to get the environment instance"""
        return get_object_or_404(Environment, pk=pk)

    def get(self, request, pk):
        """Retrieve a specific environment"""
        environment = self.get_object(pk)
        serializer = EnvironmentSerializer(environment)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, pk):
        """Fully update an environment"""
        environment = self.get_object(pk)
        serializer = EnvironmentSerializer(environment, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                serializer.data, status=status.HTTP_200_OK
            )
        return Response(
            serializer.errors, status=status.HTTP_400_BAD_REQUEST
        )

    def patch(self, request, pk):
        """Partially update an environment"""
        environment = self.get_object(pk)
        serializer = EnvironmentSerializer(
            environment, data=request.data, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(
            serializer.errors, status=status.HTTP_400_BAD_REQUEST
        )

    def delete(self, request, pk):
        """Delete an environment"""
        environment = self.get_object(pk)
        environment.delete()
        return Response(
            {"message": "Environment deleted successfully"},
            status=status.HTTP_204_NO_CONTENT
        )
