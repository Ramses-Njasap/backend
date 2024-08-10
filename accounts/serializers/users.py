from rest_framework import serializers

from utilities.models.fields import validation
# from utilities.serializers.mixins import TimeZoneConvertMixin
from utilities import response
from utilities.generators.otp import OTPGenerator

from accounts.models.users import User
from accounts.models.account import PhoneNumberVerificationOTP, EmailVerificationOTP

import time, base64


# To User TimeZoneConvertMixin in your serializer class, use like this
# class ModelSerializer(TimeZoneConvertMixin, serializers.ModelSerializer):
    # pass

class UserSerializer(serializers.ModelSerializer):

    query_id = serializers.SerializerMethodField()

    def get_query_id(self, obj):
        # Assuming that `obj.query_id` contains the binary data
        binary_data = obj.query_id
        if binary_data:
            # Encode the binary data to Base64
            return base64.b64encode(binary_data).decode('utf-8')
        return None

    class Meta:
        model = User
        fields = ('user_type', 'username', 'email', 'phone', 'is_staff', 'is_admin', 'is_superuser',
                  'is_verified', 'is_mlm_user', 'is_external_user', 'is_account_visible',
                  'is_account_locked', 'is_online', 'is_account_blocked', 'is_account_deleted',
                  'datetime_joined', 'datetime_updated', 'last_login', 'last_logout', 'query_id', 'password')
                
        read_only_fields = (
            'is_staff', 'is_admin', 'is_superuser', 'is_active', 'is_verified', 'datetime_joined',
            'datetime_updated', 'last_login', 'last_logout', 'query_id'
        )

        extra_kwargs = {
            'user_type': {'required': False},
            'username': {'required': False},
            'phone': {'required': False},
            'password': {
                'write_only': True
            }
        }

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        # This manipulates the visible of `query_id` in requests.
        # User `id` should not be visible no matter what the circumstance is
        # since it identifies an entire `Object` model instance so it can be used
        # to manipulate an entire `Object` model instance by intruder without having sufficient information.
        # `id` or `pk` values are easy to memorize and guessable so, in itself, it is not secure.
        # `query_id` field are unique values through out `Object` models the same as `id or pk` values
        # and difficult to memorize and guessable (since it's a long string/binary-string of characters), so, it serves as an acting
        # `pk or id` at the level of the application (leaving aside the database which is another topic on its own).
        # Though difficult to memorize and guess and also it is difficult to use outside of the application to access values
        # on the database because as it leaves the database, the value becomes encrypted, it is still safe to only expose it
        # at times when it is severly needed. So, this at first level, helps to manipulate its visibility to external authorised applications.
        if instance._pk_hidden:
            representation.pop("query_id")

        return representation
    
    def validate_email(self, value: str) -> str:

        email_validation = validation.EmailValidation(value).validate_or_raise()
        
        return email_validation
    
    def validate_phone(self, value: str) -> str:

        phone_validation = validation.PhoneValidation(value).validate_or_raise()
            
        return phone_validation
    
    # Cannot use validate_password function name since it is already an inbuilt serializer function name
    # following the serializer validate function naming pattern validate_{field_name}
    def validate_user_password(self, value: str, validated_data = None):
        if validated_data:
            filtered_data = {key: value for key, value in validated_data.items() if key != 'password'}

            validate_password = validation.PasswordValidation(value, filtered_data)
        
        else:
            validate_password = validation.PasswordValidation(value)

        # Check password validation
        password_validation = validate_password.validate_or_raise()

        return password_validation

    def create(self, validated_data):
        email = validated_data.get('email', None)
        phone = validated_data.pop('phone', None)
        password = validated_data.pop('password', None)

        # Checks if any of the field (email, password) is None
        # then throws an error message
        if not phone or not password:
            response.errors(
                field_error="Email/Phone or Password field missing",
                for_developer="Email/Phone or Password field missing in the request",
                code="BAD_REQUEST",
                status_code=400
            )
        
        """
        --> Validation block
        1) `field_name`_validation[0] = validation boolean value (True, False)
        2) `field_name`_validation[1] = validation code
        3) `field_name`_validation[2] = validation status code
        """
        
        # Validating password field.
        if password:
            password = self.validate_user_password(password, validated_data)
        
        # Create (new) user instance
        user_instance = User.create_user(phone=phone, **validated_data)
        user_instance.set_password(password)

        if email:

            otp = OTPGenerator(secret_key=user_instance.get_secret_key, model=EmailVerificationOTP, user=user_instance)
            otp.generate_otp()

        else:
            otp = OTPGenerator(secret_key=user_instance.get_secret_key, model=PhoneNumberVerificationOTP, user=user_instance)
            otp.generate_otp()

        return user_instance