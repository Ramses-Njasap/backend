from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from accounts.models.plans import SubscriptionPlan, UserSubscriptionPlan

from accounts.serializers.users import UserSerializer

from utilities import response
from utilities.json.encoders import DecimalEncoder

import json


class BasicSubscriptionPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionPlan
        fields = ('id', 'name', 'storage_space', 'consultation_hours', 'sale_deduction', 'rental_deduction',
                  'new_user_commission', 'sales_commission', 'rental_commission')
        read_only_fields = ('id',)


class SubscriptionPlanSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = SubscriptionPlan
        fields = ('id', 'name',  'description', 'is_active', 'price', 'storage_space',
                  'consultation_hours', 'sale_deduction', 'rental_deduction', 'new_user_commission',
                  'sales_commission', 'rental_commission')
        read_only_fields = ('id',)

    def to_representation(self, instance):
        excluded_fields = ['id', 'name', 'description', 'is_active']
        
        representation = super().to_representation(instance)

        for field_name in self.Meta.fields:
            if field_name not in excluded_fields:
                value = getattr(instance, field_name)
                representation[field_name] = json.loads(json.dumps(value, cls=DecimalEncoder))
        
        representation["features"] = {}
        for field_name in self.Meta.fields:
            if field_name not in excluded_fields:
                field = f"get_{field_name}"
                try:
                    value = getattr(instance, field)
                    representation["features"][field] = value
                except AttributeError:
                    # Handle the case where the field is not found in the model
                    pass
            
        return representation


class UserSubscriptionPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserSubscriptionPlan
        fields = ('id', 'user', 'plan', 'duration', 'formatted_duration', 'custom_plans', 'total_price', 'formatted_price')
        read_only_fields = ('id', 'total_price', 'formatted_duration', 'formatted_price')
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
            except:
                # setting error messages for user and developer respectively
                field_message = f'`duration` key should be of type integer and not {type(duration)}'
                for_developer = f'`duration` key should be of type integer and not {type(duration)}'
                
                # Raising error responses
                response.errors(field_error=field_message, for_developer=for_developer, code="BAD_REQUEST", status_code=400)

        # Using a conditional expression (ternary operator) to determine the period and duration
        # If duration is less than 12, set both duration_period and duration to duration and 'MONTHLY', respectively.
        # If duration is 12 or more, calculate the number of years (duration_period) and set duration to 'YEARLY'.
        if duration == 0:
            duration_period, duration = (duration, "LIFE TIME")
        else:
            duration_period, duration = (duration, 'MONTHLY') if duration < 12 else (duration // 12, 'YEARLY')

        try:
            plan_instance = UserSubscriptionPlan.objects.create(user=user, plan=plan, duration=duration.upper(), duration_period=duration_period)
        except Exception as e:
            # setting error messages for user and developer respectively
            field_message = "Account Creation Process Cancelled. Failed To Create Subsrciption Plan"
            for_developer = str(e)

            # Raising error responses
            response.errors(field_error=field_message, for_developer=for_developer, code="NOT_CREATED",
                            status_code=501)

        return plan_instance