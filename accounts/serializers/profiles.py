from rest_framework import serializers
from accounts.models.profiles import UserProfile, Group

from accounts.serializers.users import UserSerializer


class GroupSerializer(serializers.ModelField):
    class Meta:
        models = Group
        fields = ("_type", "base_group",)


class UserProfileSerializer(serializers.ModelSerializer):
    first_name = serializers.SerializerMethodField()
    last_name = serializers.SerializerMethodField()

    class Meta:
        model = UserProfile
        fields = ("statuses", "user", "groups", "phone", "legal_name", "first_name", "last_name",
                  "gender", "date_of_birth")

    def get_first_name(self, obj):
        if obj.legal_name:
            return obj.legal_name.split()[0]
        return None

    def get_last_name(self, obj):
        if obj.legal_name:
            name_parts = obj.legal_name.split()
            if len(name_parts) > 1:
                return name_parts[-1]
        return None
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation["user"] = UserSerializer(instance.user).data
        # representation["groups"] = GroupSerializer(instance.groups.all(), many=True).data
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