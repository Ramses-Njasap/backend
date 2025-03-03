from rest_framework import serializers
from properties.models.environments import Environment
from properties.models.lands import LandProperty
from properties.serializers.environments import EnvironmentSerializer


class LandPropertySerializer(serializers.ModelSerializer):
    # Nesting the EnvironmentSerializer
    environment = EnvironmentSerializer(read_only=True)

    class Meta:
        model = LandProperty
        fields = ["id", "environment"]

    def to_representation(self, instance):
        """Customize the response to include environment details"""
        representation = super().to_representation(instance)
        if instance.environment:
            representation["environment"] = EnvironmentSerializer(
                instance.environment
            ).data
        return representation

    def validate(self, attrs):
        """Ensure environment is not already linked to another LandProperty"""
        environment_id = self.initial_data.get("environment")
        if LandProperty.objects.filter(
            environment_id=environment_id
        ).exists():
            raise serializers.ValidationError(
                "This environment is already linked to a land property."
            )
        return attrs

    def create(self, validated_data):
        """Override create method to explicitly set environment"""
        environment_id = self.initial_data.get("environment")
        environment = Environment.objects.get(id=environment_id)
        return LandProperty.objects.create(environment=environment)
