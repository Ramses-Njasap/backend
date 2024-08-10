from rest_framework import serializers
from django.utils import timezone

class TimeZoneConvertMixin:
    def to_representation(self, instance):
        representation = super().to_representation(instance)

        # Convert datetime, date, and time fields to user's timezone
        for field_name, field in self.fields.items():
            if isinstance(field, (serializers.DateTimeField, serializers.DateField, serializers.TimeField)) and field_name in representation:
                if isinstance(field, serializers.DateTimeField):
                    representation[field_name] = timezone.localtime(
                        representation[field_name]
                    ).strftime('%Y-%m-%d %H:%M:%S')
                elif isinstance(field, serializers.DateField):
                    representation[field_name] = timezone.localtime(
                        representation[field_name]
                    ).strftime('%Y-%m-%d')
                elif isinstance(field, serializers.TimeField):
                    representation[field_name] = timezone.localtime(
                        representation[field_name]
                    ).strftime('%H:%M:%S')

        return representation