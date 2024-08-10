from rest_framework import serializers

from utilities.validation import Validate
from utilities import response


class EmailOrPhoneSerializer(serializers.CharField):
    def to_internal_value(self, data):
        value = super().to_internal_value(data)
        
        # Creating Validation Instance for `value`
        validate = Validate(value)
        
        if validate.phone:
            return value
        
        elif validate.email:
            return value
        
        else:
            # setting error messages for user and developer respectively
            field_message = "Invalid Email Or Phone Number Value/Input"
            for_developer = "Email/Phone Number Matching Failed. Invalid Email/Phone Number"
            
            # Raising error responses
            response.errors(field_error=field_message, for_developer=for_developer, code="NOT_FOUND", status_code=404)
