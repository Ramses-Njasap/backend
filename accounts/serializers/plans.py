from rest_framework import serializers

from accounts.models.plans import SubscriptionPlan, UserSubscriptionPlan

from accounts.serializers.users import UserSerializer

from utilities import response

from decimal import Decimal
from accounts.models.plans import (
    DefaultFeature, AIConflictResolutionAssistantFeature, TeamGoalFeature,
    AIMarketingAssistantFeature, MultiLevelMarketingFeature, BusinessFeature
)


class DefaultFeatureSerializer(serializers.ModelSerializer):
    """
    Detailed serializer for the DefaultFeature model with additional
    validations, custom creation logic, and computed properties.
    """

    # Computed fields
    invite_price = serializers.SerializerMethodField()
    invite_commission_price = serializers.SerializerMethodField()
    price = serializers.SerializerMethodField()
    get_invite_commission = serializers.CharField(
        read_only=True,
    )

    class Meta:
        model = DefaultFeature
        fields = ("id", "_type", "is_custom", "name", "buyer",
                  "max_invite", "get_invite_commission",
                  "invite_price", "invite_commission_price", "price")
        read_only_fields = ("price", "get_invite_commission")

    def get_invite_price(self, obj):
        """
        Calculate invite price dynamically based on the user passed
        in the serializer context.
        """
        user = self._get_user_context()
        return obj.invite_price(user=user)

    def get_invite_commission_price(self, obj):
        """
        Calculate invite price dynamically based on the user passed
        in the serializer context.
        """
        user = self._get_user_context()
        return obj.invite_commission_price(user=user)

    def get_price(self, obj):
        """
        Calculate the price dynamically based on the user passed
        in the serializer context.
        """
        user = self._get_user_context()

        return obj.price(user=user)

    def validate_name(self, value):
        """
        Ensure the feature name is unique across the same `_type`.
        """
        _type = self.initial_data.get("_type", "").upper()
        if DefaultFeature.objects.filter(name=value, _type=_type).exists():
            raise serializers.ValidationError(
                f"A feature with the name '{value}' already exists for type '{_type}'."
            )
        return value

    def validate_invite_commission(self, value):
        """
        Ensure the invite commission is non-negative.
        """
        if value < Decimal("0.00"):
            raise serializers.ValidationError(
                "Invite commission must be a non-negative value."
            )
        return value

    def validate_max_invite(self, value):
        """
        Ensure the max_invite is not less than the minimum allowed (2).
        """
        if value < 2:
            raise serializers.ValidationError(
                "Maximum invite must be at least 2."
            )
        return value

    def validate(self, data):
        """
        Perform cross-field validation.
        Ensure `_type` is valid and matches internal/external logic.
        """
        _type = data.get("_type", "").upper()
        if _type not in dict(DefaultFeature.FeatureBelongsTo.choices):
            raise serializers.ValidationError(
                {"_type": f"Invalid feature type '{_type}'."}
            )
        return data

    def create(self, validated_data):
        """
        Custom create method to handle any additional logic.
        """
        # Ensure `_type` is converted to uppercase
        validated_data["_type"] = validated_data["_type"].upper()
        return super().create(validated_data)

    def update(self, instance, validated_data):
        """
        Custom update method to handle updates while preserving business rules.
        """
        # Ensure `_type` is converted to uppercase
        if "_type" in validated_data:
            validated_data["_type"] = validated_data["_type"].upper()

        # Apply the update and return the updated instance
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        """
        Customize the representation of the serialized data.
        This can be useful for formatting output differently.
        """
        representation = super().to_representation(instance)
        representation["feature_details"] = f"{instance.name} ({instance._type})"
        return representation

    def _get_user_context(self):
        """
        Utility function to retrieve user from the context.
        Raises an error if user is not provided.
        Space Complexity: O(1)
        Time Complexity: O(1)
        """
        user = self.context.get("user", None)

        return user


class AIConflictResolutionAssistantFeatureSerializer(
    serializers.ModelSerializer
):
    """
    Detailed serializer for the AIConflictResolutionAssistantFeature
    model with additional validations, custom creation logic, and
    computed properties.
    """

    # Computed fields
    price = serializers.SerializerMethodField()

    class Meta:
        model = AIConflictResolutionAssistantFeature
        fields = ("id", "_type", "is_custom", "name", "max_conflict",
                  "max_conflict_price", "price")

    def get_price(self, obj):
        """
        Calculate the price dynamically based on the user passed
        in the serializer context.
        """
        user = self._get_user_context()
        return obj.price(user=user)

    def validate_name(self, value):
        """
        Ensure the feature name is unique across the same `_type`.
        """
        _type = self.initial_data.get("_type", "").upper()
        if AIConflictResolutionAssistantFeature.objects.filter(
            name=value, _type=_type
        ).exists():
            raise serializers.ValidationError(
                f"A feature with the name '{value}' already exists for type '{_type}'."
            )
        return value

    def validate_max_conflict(self, value):
        """
        Ensure the max conflict is not less than one.
        """
        if value < Decimal("1.00"):
            raise serializers.ValidationError(
                "Max conflict must be greater than or equal to one."
            )
        return value

    def validate(self, data):
        """
        Perform cross-field validation.
        Ensure `_type` is valid and matches internal/external logic.
        """
        _type = data.get("_type", "").upper()
        if _type not in dict(
            AIConflictResolutionAssistantFeature.FeatureBelongsTo.choices
        ):
            raise serializers.ValidationError(
                {"_type": f"Invalid feature type '{_type}'."}
            )
        return data

    def create(self, validated_data):
        """
        Custom create method to handle any additional logic.
        """
        # Ensure `_type` is converted to uppercase
        validated_data["_type"] = validated_data["_type"].upper()
        return super().create(validated_data)

    def update(self, instance, validated_data):
        """
        Custom update method to handle updates while preserving business rules.
        """
        # Ensure `_type` is converted to uppercase
        if "_type" in validated_data:
            validated_data["_type"] = validated_data["_type"].upper()

        # Apply the update and return the updated instance
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        """
        Customize the representation of the serialized data.
        This can be useful for formatting output differently.
        """
        user = self._get_user_context()
        representation = super().to_representation(instance)
        representation["feature_details"] = f"{instance.name} ({instance._type})"

        precomputed_prices = {
            "max_conflict_price": instance.max_conflict_price(user),
        }

        # Add precomputed values to the representation
        representation["max_conflict"] = {
            "value": getattr(instance, "get_max_conflict", None),
            "price": precomputed_prices["max_conflict_price"],
        }

        # Remove unnecessary fields
        fields_to_remove = [
            "max_conflict_price",
        ]
        for field in fields_to_remove:
            representation.pop(field, None)

        representation["feature_details"] = f"{instance.name} ({instance._type})"
        return representation

    def _get_user_context(self):
        """
        Utility function to retrieve user from the context.
        Raises an error if user is not provided.
        Space Complexity: O(1)
        Time Complexity: O(1)
        """
        user = self.context.get("user", None)

        return user


class TeamGoalFeatureSerializer(
    serializers.ModelSerializer
):
    """
    Detailed serializer for the TeamGoalFeature model
    with additional validations, custom creation logic, and
    computed properties.
    """

    # Computed fields
    price = serializers.SerializerMethodField()

    class Meta:
        model = TeamGoalFeature
        fields = ("id", "_type", "is_custom", "name",
                  "conflict_resolver", "max_team",
                  "max_team_price", "price")

    def get_price(self, obj):
        """
        Calculate the price dynamically based on the user passed
        in the serializer context.
        """
        user = self._get_user_context()

        return obj.price(user=user)

    def validate_name(self, value):
        """
        Ensure the feature name is unique across the same `_type`.
        """
        _type = self.initial_data.get("_type", "").upper()
        if TeamGoalFeature.objects.filter(
            name=value, _type=_type
        ).exists():
            raise serializers.ValidationError(
                f"A feature with the name '{value}' already exists for type '{_type}'."
            )
        return value

    def validate(self, data):
        """
        Perform cross-field validation.
        Ensure `_type` is valid and matches internal/external logic.
        """
        _type = data.get("_type", "").upper()
        if _type not in dict(
            TeamGoalFeature.FeatureBelongsTo.choices
        ):
            raise serializers.ValidationError(
                {"_type": f"Invalid feature type '{_type}'."}
            )
        return data

    def create(self, validated_data):
        """
        Custom create method to handle any additional logic.
        """
        # Ensure `_type` is converted to uppercase
        validated_data["_type"] = validated_data["_type"].upper()
        return super().create(validated_data)

    def update(self, instance, validated_data):
        """
        Custom update method to handle updates while preserving business rules.
        """
        # Ensure `_type` is converted to uppercase
        if "_type" in validated_data:
            validated_data["_type"] = validated_data["_type"].upper()

        # Apply the update and return the updated instance
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        """
        Customize the representation of the serialized data.
        This can be useful for formatting output differently.
        """
        user = self._get_user_context()
        representation = super().to_representation(instance)
        # Handle the conflict_resolver relation
        if hasattr(instance, "conflict_resolver") and instance.conflict_resolver:
            representation["conflict_resolver"] = (
                AIConflictResolutionAssistantFeatureSerializer(
                    instance=instance.conflict_resolver,
                    context={
                        "user": user
                    }
                ).data
            )
        else:
            representation["conflict_resolver"] = None

        precomputed_prices = {
            "max_team_price": instance.max_team_price(user),
        }

        # Add precomputed values to the representation
        representation["max_team"] = {
            "value": getattr(instance, "get_max_team", None),
            "price": precomputed_prices["max_team_price"],
        }

        # Remove unnecessary fields
        fields_to_remove = [
            "max_team_price",
        ]
        for field in fields_to_remove:
            representation.pop(field, None)

        representation["feature_details"] = f"{instance.name} ({instance._type})"
        return representation

    def _get_user_context(self):
        """
        Utility function to retrieve user from the context.
        Raises an error if user is not provided.
        Space Complexity: O(1)
        Time Complexity: O(1)
        """
        user = self.context.get("user", None)

        return user


class AIMarketingAssistantFeatureSerializer(
    serializers.ModelSerializer
):
    """
    Detailed serializer for the TeamGoalFeature model
    with additional validations, custom creation logic, and
    computed properties.
    """

    # Computed fields
    price = serializers.SerializerMethodField()

    class Meta:
        model = AIMarketingAssistantFeature
        fields = ("id", "_type", "is_custom", "name",
                  "max_rounds", "max_rounds_price", "price")

    def get_price(self, obj):
        """
        Calculate the price dynamically based on the user passed
        in the serializer context.
        """
        user = self._get_user_context()
        return obj.price(user=user)

    def validate_name(self, value):
        """
        Ensure the feature name is unique across the same `_type`.
        """
        _type = self.initial_data.get("_type", "").upper()
        if AIMarketingAssistantFeature.objects.filter(
            name=value, _type=_type
        ).exists():
            raise serializers.ValidationError(
                f"A feature with the name '{value}' already exists for type '{_type}'."
            )
        return value

    def validate_max_rounds(self, value):
        """
        Ensure the max rounds is not less than one.
        """
        if value < Decimal("2.00"):
            raise serializers.ValidationError(
                "Max rounds must be greater than or equal to 2."
            )
        return value

    def validate(self, data):
        """
        Perform cross-field validation.
        Ensure `_type` is valid and matches internal/external logic.
        """
        _type = data.get("_type", "").upper()
        if _type not in dict(
            AIMarketingAssistantFeature.FeatureBelongsTo.choices
        ):
            raise serializers.ValidationError(
                {"_type": f"Invalid feature type '{_type}'."}
            )
        return data

    def create(self, validated_data):
        """
        Custom create method to handle any additional logic.
        """
        # Ensure `_type` is converted to uppercase
        validated_data["_type"] = validated_data["_type"].upper()
        return super().create(validated_data)

    def update(self, instance, validated_data):
        """
        Custom update method to handle updates while preserving business rules.
        """
        # Ensure `_type` is converted to uppercase
        if "_type" in validated_data:
            validated_data["_type"] = validated_data["_type"].upper()

        # Apply the update and return the updated instance
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        """
        Customize the representation of the serialized data.
        This can be useful for formatting output differently.
        """

        user = self._get_user_context()
        representation = super().to_representation(instance)

        precomputed_prices = {
            "max_rounds_price": instance.max_rounds_price(user),
        }

        # Add precomputed values to the representation
        representation["max_rounds"] = {
            "value": getattr(instance, "get_max_rounds", None),
            "price": precomputed_prices["max_rounds_price"],
        }

        representation["feature_details"] = f"{instance.name} ({instance._type})"

        # Remove unnecessary fields
        fields_to_remove = [
            "max_rounds_price",
        ]
        for field in fields_to_remove:
            representation.pop(field, None)

        return representation

    def _get_user_context(self):
        """
        Utility function to retrieve user from the context.
        Raises an error if user is not provided.
        Space Complexity: O(1)
        Time Complexity: O(1)
        """
        user = self.context.get("user", None)

        return user


class MultiLevelMarketingFeatureSerializer(serializers.ModelSerializer):
    """
    Serializer for the MultiLevelMarketingFeature model.
    Optimized for readability, maintainability, and efficiency.
    """

    # Computed fields
    price = serializers.SerializerMethodField()

    class Meta:
        model = MultiLevelMarketingFeature
        fields = (
            "id", "_type", "is_custom", "name",
            "sale_commission", "rental_commission",
            "sale_commission_price", "rental_commission_price",
            "price",
        )
        extra_kwargs = {
            "sale_commission": {"write_only": True},
            "rental_commission": {"write_only": True},
        }

    def get_price(self, obj):
        """
        Calculate the price dynamically based on the user passed
        in the serializer context.
        Space Complexity: O(1) (minimal space used)
        Time Complexity: O(1) (direct method call)
        """
        user = self._get_user_context()
        return obj.price(user=user)

    def validate_name(self, value):
        """
        Ensure the feature name is unique for a given `_type`.
        Space Complexity: O(1) (query does not store data in memory)
        Time Complexity: O(1) (indexed lookup, assuming database indexing)
        """
        _type = self.initial_data.get("_type", "").upper()
        if MultiLevelMarketingFeature.objects.filter(name=value, _type=_type).exists():
            raise serializers.ValidationError(
                f"A feature with the name '{value}' already exists for type '{_type}'."
            )
        return value

    def validate(self, data):
        """
        Cross-field validation to ensure `_type` is valid.
        Space Complexity: O(1)
        Time Complexity: O(1)
        """
        _type = data.get("_type", "").upper()
        if _type not in dict(MultiLevelMarketingFeature.FeatureBelongsTo.choices):
            raise serializers.ValidationError(
                {"_type": f"Invalid feature type '{_type}'."}
            )
        data["_type"] = _type  # Normalize `_type` here
        return data

    def create(self, validated_data):
        """
        Custom create logic for `_type` normalization.
        Space Complexity: O(1)
        Time Complexity: O(1)
        """
        return super().create(validated_data)

    def update(self, instance, validated_data):
        """
        Custom update logic for `_type` normalization.
        Space Complexity: O(1)
        Time Complexity: O(1)
        """
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        """
        Customize the serialized representation.
        Space Complexity: O(1) (no additional storage required)
        Time Complexity: O(1) (one database hit for precomputed prices)
        """
        user = self._get_user_context()
        representation = super().to_representation(instance)

        precomputed_prices = {
            "sale_commission_price": instance.sale_commission_price(user),
            "rental_commission_price": instance.rental_commission_price(user),
        }

        # Add precomputed values to the representation
        representation.update({
            "sale_commission": {
                "value": getattr(instance, "get_sale_commission", None),
                "price": precomputed_prices["sale_commission_price"],
            },
            "rental_commission": {
                "value": getattr(instance, "get_rental_commission", None),
                "price": precomputed_prices["rental_commission_price"],
            },
            "feature_details": f"{instance.name} ({instance._type})"
        })

        # Remove unnecessary fields
        fields_to_remove = [
            "sale_commission_price", "rental_commission_price",
        ]
        for field in fields_to_remove:
            representation.pop(field, None)

        return representation

    def _get_user_context(self):
        """
        Utility function to retrieve user from the context.
        Raises an error if user is not provided.
        Space Complexity: O(1)
        Time Complexity: O(1)
        """
        user = self.context.get("user", None)

        return user


class BusinessFeatureSerializer(serializers.ModelSerializer):
    """
    Optimized serializer for the BusinessFeature model
    with reduced overhead in computed fields and representations.
    """
    # Precompute fields
    price = serializers.SerializerMethodField()

    class Meta:
        model = BusinessFeature
        fields = ("id", "_type", "is_custom", "name", "seller",
                  "sale_deduction", "rental_deduction", "storage_space",
                  "consultation_hours", "marketing_assistant", "mlm_feature",
                  "sale_deduction_price", "rental_deduction_price",
                  "storage_space_price", "consultation_hours_price", "price")
        extra_kwargs = {
            "sale_deduction": {"write_only": True},
            "rental_deduction": {"write_only": True},
            "storage_space": {"write_only": True},
            "consultation_hours": {"write_only": True},
        }

    def get_price(self, obj):
        """
        Calculate the total price dynamically based on the user.
        """
        user = self._get_user_context()

        return obj.price(user=user)

    def to_representation(self, instance):
        """
        Optimize the restructuring of fields and computed data.
        """
        user = self._get_user_context()
        precomputed_prices = {
            "sale_deduction_price": instance.sale_deduction_price(user),
            "rental_deduction_price": instance.rental_deduction_price(user),
            "storage_space_price": instance.storage_space_price(user),
            "consultation_hours_price": instance.consultation_hours_price(user),
        }

        # Precomputed values for a single database hit
        representation = super().to_representation(instance)
        representation["sale_deduction"] = {
            "value": getattr(instance, "get_sale_deduction", None),
            "price": precomputed_prices["sale_deduction_price"],
        }
        representation["rental_deduction"] = {
            "value": getattr(instance, "get_rental_deduction", None),
            "price": precomputed_prices["rental_deduction_price"],
        }
        representation["storage_space"] = {
            "value": getattr(instance, "get_storage_space", None),
            "price": precomputed_prices["storage_space_price"],
        }
        representation["consultation_hours"] = {
            "value": getattr(instance, "get_consultation_hours", None),
            "price": precomputed_prices["consultation_hours_price"],
        }

        if hasattr(instance, "marketing_assistant") and instance.marketing_assistant:
            representation["marketing_assistant"] = (
                AIMarketingAssistantFeatureSerializer(
                    instance=instance.marketing_assistant,
                    context={
                        "user": user
                    }
                ).data
            )
        else:
            representation.pop("marketing_assistant", None)

        if hasattr(instance, "mlm_feature") and instance.mlm_feature:
            representation["mlm_feature"] = (
                MultiLevelMarketingFeatureSerializer(
                    instance=instance.mlm_feature,
                    context={
                        "user": user
                    }
                ).data
            )
        else:
            representation.pop("mlm_feature", None)

        representation["feature_details"] = f"{instance.name} ({instance._type})"

        # Remove unnecessary fields
        fields_to_remove = [
            "sale_deduction_price", "rental_deduction_price",
            "storage_space_price", "consultation_hours_price",
        ]
        for field in fields_to_remove:
            representation.pop(field, None)

        return representation

    def validate_name(self, value):
        """
        Optimize validation by caching `_type` and reusing logic.
        """
        _type = self.initial_data.get("_type", "").upper()
        if MultiLevelMarketingFeature.objects.filter(name=value, _type=_type).exists():
            raise serializers.ValidationError(
                f"A feature with the name '{value}' already exists for type '{_type}'."
            )
        return value

    def validate(self, data):
        """
        Cross-field validation with efficient `_type` lookup.
        """
        _type = data.get("_type", "").upper()
        valid_types = dict(BusinessFeature.FeatureBelongsTo.choices)
        if _type not in valid_types:
            raise serializers.ValidationError(
                {"_type": f"Invalid feature type '{_type}'."}
            )
        return data

    def create(self, validated_data):
        """
        Efficient `_type` handling during creation.
        """
        validated_data["_type"] = validated_data["_type"].upper()
        return super().create(validated_data)

    def update(self, instance, validated_data):
        """
        Efficient `_type` handling during updates.
        """
        if "_type" in validated_data:
            validated_data["_type"] = validated_data["_type"].upper()
        return super().update(instance, validated_data)

    def _get_user_context(self):
        """
        Utility function to retrieve user from the context.
        Raises an error if user is not provided.
        Space Complexity: O(1)
        Time Complexity: O(1)
        """
        user = self.context.get("user", None)

        return user


class BasicSubscriptionPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionPlan
        fields = ('id', 'name', 'storage_space',
                  'consultation_hours', 'sale_deduction', 'rental_deduction',
                  'new_user_commission', 'sales_commission', 'rental_commission')
        read_only_fields = ('id',)


class SubscriptionPlanSerializer(serializers.ModelSerializer):

    price = serializers.SerializerMethodField()

    class Meta:
        model = SubscriptionPlan
        fields = (
            "_type", "is_custom", "name", "description",
            "is_active", "default_feature", "team_feature",
            "business_feature", "price"
        )
        read_only_fields = ('id',)

    def get_price(self, obj):
        """
        Calculate the total price dynamically based on the user.
        """
        user = self._get_user_context()
        return obj.price(user=user)

    def to_representation(self, instance):

        user = self._get_user_context()
        representation = super().to_representation(instance)

        if hasattr(instance, "default_feature") and instance.default_feature:
            representation["default_feature"] = (
                DefaultFeatureSerializer(
                    instance=instance.default_feature,
                    context={
                        "user": user
                    }
                ).data
            )
        else:
            representation.pop("default_feature", None)

        if hasattr(instance, "team_feature") and instance.team_feature:
            representation["team_feature"] = (
                TeamGoalFeatureSerializer(
                    instance=instance.team_feature,
                    context={
                        "user": user
                    }
                ).data
            )
        else:
            representation.pop("team_feature", None)

        if hasattr(instance, "business_feature") and instance.business_feature:
            representation["business_feature"] = (
                BusinessFeatureSerializer(
                    instance=instance.business_feature,
                    context={
                        "user": user
                    }
                ).data
            )
        else:
            representation.pop("business_feature", None)

        return representation

    def _get_user_context(self):
        """
        Utility function to retrieve user from the context.
        Raises an error if user is not provided.
        Space Complexity: O(1)
        Time Complexity: O(1)
        """
        user = self.context.get("user", None)

        return user


class UserSubscriptionPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserSubscriptionPlan
        fields = ('id', 'user', 'plan', 'duration', 'formatted_duration',
                  'custom_plans', 'total_price', 'formatted_price')
        read_only_fields = ('id', 'total_price', 'formatted_duration',
                            'formatted_price')
        extra_kwargs = {
            'custom_plans': {'required': False},
        }

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        representation["user"] = UserSerializer(instance.user).data

        representation["plan"] = SubscriptionPlanSerializer(instance.plan).data

        return representation

    def create(self, validated_data):
        user = validated_data.pop('user', None)
        plan = validated_data.pop("plan", None)

        duration = self.context['data'].get('duration_length', None)

        if not isinstance(duration, int):
            try:
                duration = int(duration)
            except (ValueError, TypeError):
                # setting error messages for user and developer respectively
                field_message = (f"""`duration` key should be of type
                                 integer and not {type(duration)}""")
                for_developer = (f"""`duration` key should be of type
                                 integer and not {type(duration)}""")

                # Raising error responses
                response.errors(field_error=field_message,
                                for_developer=for_developer,
                                code="BAD_REQUEST", status_code=400)

        # Using a conditional expression (ternary operator)
        # to determine the period and duration
        # If duration is less than 12, set both duration_period
        # and duration to duration and 'MONTHLY', respectively.
        # If duration is 12 or more, calculate the number
        # of years (duration_period) and set duration to 'YEARLY'.
        if duration == 0:
            duration_period, duration = (duration, "LIFE TIME")
        else:
            if duration < 12:
                duration_period, duration = duration, 'MONTHLY'
            else:
                duration_period, duration = duration // 12, 'YEARLY'

        try:
            plan_instance = UserSubscriptionPlan.objects.create(
                user=user, plan=plan, duration=duration.upper(),
                duration_period=duration_period)

        except Exception as e:
            # setting error messages for user and developer respectively
            field_message = ("Account Creation Process Cancelled."
                             " Failed To Create Subsrciption Plan")
            for_developer = str(e)

            # Raising error responses
            response.errors(field_error=field_message,
                            for_developer=for_developer,
                            code="NOT_CREATED",
                            status_code=501)

        return plan_instance
