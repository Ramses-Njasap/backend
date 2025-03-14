from rest_framework import serializers

from properties.models.profiles import UserProfile

from accounts.serializers.profiles import (
    UserProfileSerializer as AccountUserProfileSerializer
)


class ProfileSerializer(serializers.ModelSerializer):
    first_name = serializers.SerializerMethodField()
    last_name = serializers.SerializerMethodField()

    class Meta:
        model = UserProfile
        fields = ("statuses", "user", 'user_type')

    def name(self, obj):

        name = obj.user.legalname if obj.user.legalname else obj.name

        return obj.name if obj.name else name

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation["user"] = AccountUserProfileSerializer(instance.user).data
        return representation

    def create(self, validated_data):
        """
        Create and return a new UserProfile instance.

        Args:
            validated_data (dict): Validated data from the request.

        Returns:
            UserProfile: Created UserProfile instance.
        """
        user_profile = UserProfile.objects.create(**validated_data)
        return user_profile

    def update(self, instance, validated_data):
        """
        Update and return an existing UserProfile instance.

        Args:
            instance (UserProfile): The existing UserProfile instance to update.
            validated_data (dict): Validated data from the request.

        Returns:
            UserProfile: Updated UserProfile instance.
        """
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance

    def partial_update(self, instance, validated_data):
        """Handles partial update of a Profile instance (PATCH)."""
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance

    def delete(self, instance):
        """Handles deletion of a Profile instance (DELETE)."""
        instance.delete()
