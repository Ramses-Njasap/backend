from utilities import response
from utilities.models.relationship_checker import ModelRelationshipChecker
from utilities.account import OTP as _OTP

from accounts.models.account import OTP, UsedOTP, OTPModels
from accounts.models.auth import AuthCredential

from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db import models

import hashlib
import time
import random


class OTPGenerator:
    def __init__(self, secret_key: str, model: models.Model, user: AuthCredential = None, req: bool = False, save: bool = True):
        self.secret_key = secret_key
        self.model = model
        self.user = user
        self.req = req
        self.save = save

    def generate_otp(self):

        # check if model is valid for this operation
        _otp_instance = _OTP(self.model)

        if not _otp_instance._check_model_validity():
            # Raising errors
            response.errors(
                field_error="Invalid Model",
                for_developer=f"Model ({self.model._meta.model_name}) Not A Valid Model For This Operation. Valid Models Are {dir(OTPModels)}",
                code="INTERNAL_SERVER_ERROR",
                status_code=500
            )

        # Setting the maximum number of attempts to generate a unique OTP
        max_attempts = 10

        for _ in range(max_attempts):
            # Generating the current OTP using the current time and user_id
            current_otp = self._generate_current_otp()

            if self.save:
            # Checking if the OTP is unique across all users
                is_otp_used = self._is_otp_used(current_otp)

                if not is_otp_used[0]:
                    # If unique, mark the OTP as used and return it
                    self._mark_otp_used(current_otp, self.user)

                    return current_otp
            else:
                return current_otp

            # If not unique, try generating a new OTP

        # Raising errors
        response.errors(
            field_error="Failed To Generate Unique OTP",
            for_developer="Maximum Tries To Create Unique OTP Exceeded. OTP Generation Failed",
            code="INTERNAL_SERVER_ERROR",
            status_code=500
        )

    def _generate_current_otp(self):
        # Getting the current time in seconds
        current_time = int(time.time())

        # Defining the time step (in seconds)
        time_step = 30

        # Calculating the counter based on the current time and time step
        counter = current_time // time_step

        # Converting the counter to bytes
        counter_bytes = counter.to_bytes(8, byteorder='big')

        # Converting the secret key to bytes
        secret_key_bytes = self.secret_key.encode('utf-8')

        # Using HMAC-SHA256 for hashing
        hmac_digest = hashlib.sha256(secret_key_bytes + counter_bytes).digest()

        # Extracting the dynamic truncation offset from the last 4 bits of the digest
        offset = hmac_digest[-1] & 0x0F

        # Extracting a 4-byte dynamic binary code from the digest
        binary_code = hmac_digest[offset:offset + 4]

        # Converting the binary code to an integer and formatting to be 6 digits
        otp = int.from_bytes(binary_code, byteorder='big') % 10**6
        current_otp = f'{otp:06d}'

        return current_otp

    def _is_otp_used(self, otp: str) -> tuple:
        # Implementing the logic to check if the OTP is already used
        # This could involve checking against a database
        # If OTP does not exist, it should create a new OTP instance and save to database

        # return statements:
        # tuple[0] Does self.model instance otp exists? tuple[1] is self.model instance otp active?

        otp_instance, is_otp_created = OTP.objects.get_or_create(otp=otp)

        model_instance, is_model_created = self.model.objects.get_or_create(user=self.user)

        if not is_model_created:

            if not is_otp_created:

                used_otp_instance = model_instance.used_otp.filter(otp=otp_instance).exists()

                if used_otp_instance:

                    if used_otp_instance.first().is_active:
                        
                        # used otp instance for user in self.model exists and it is the active instance in self.model
                        return True, True
                    
                    else:
                        # used otp instance for user in self.model exists and it is not active in self.model
                        return True, False
                
            else:
                # Used OTP instance for user in self.model does not exists and cannot be active in self.model since it doesn't exist in the first place
                return False, False
        
        else:
            # The OTP exists but does not exists in self.model so all returns False
            return False, False

    def _mark_otp_used(self, otp, is_instance_active: bool = False):
        # Implement the logic to mark the OTP as used
        # This could involve storing the used OTP in a database or another storage mechanism
        # For simplicity, this example does not store the used OTPs

        # Replace this with the actual implementation
        model_instance = self.model.objects.filter(user=self.user).first()
        otp_instance = OTP.objects.get(otp=otp)

        check_relationship = self._relationship_checker()

        if check_relationship[0] == True and check_relationship[2] == models.ForeignKey.__name__:
            field_name = check_relationship[1]
        
        else:
            # Raising errors
            response.errors(
                field_error = "Relationship Nonexistent",
                for_developer = f"Model ({self.model._meta.model_name}) Has No Relationship With {OTP._meta.model_name} or Model ({self.model._meta.model_name}) Is Not A ForeignKey To {OTP._meta.model_name}",
                code = "BAD_REQUEST",
                status_code = 400
            )

        # Creating a dictionary with the dynamic field name and value
        update_dict = {field_name: model_instance, 'is_active': True}

        # Updating instances based on the dynamic field name
        UsedOTP.objects.filter(**update_dict).update(is_active=False)

        used_otp_instance = UsedOTP.objects.create(otp=otp_instance, is_active=True)

        setattr(used_otp_instance, field_name, model_instance)
        used_otp_instance.save()

        model_instance.used_otp.add(otp_instance)
        model_instance.current_otp = otp_instance
        model_instance.save()

        return
    
    def _relationship_checker(self):
        checker = ModelRelationshipChecker()
        has_relationship, field_name, relationship_type = checker.check_relationship(
            target_model_name=self.model._meta.model_name, potential_relationship_model_name='UsedOTP',
            app_label=self.model._meta.app_label, relationship_type=models.ForeignKey
        )

        return has_relationship, field_name, relationship_type
    

class OTPVerifier:
    def __init__(self, secret_key):
        self.secret_key = secret_key

    def verify_otp(self, user_otp, user_id, window=1):
        # Set the maximum number of attempts to verify the OTP within the window
        max_attempts = 10

        for _ in range(max_attempts):
            # Verify the OTP using the current time and user_id
            if self._verify_current_otp(user_otp, user_id, window):
                return True

        return False

    def _verify_current_otp(self, user_otp, user_id, window):
        # Get the current time in seconds
        current_time = int(time.time())

        # Defining the time step (in seconds)
        time_step = 30

        # Calculating the counter based on the current time and time step
        counter = current_time // time_step

        # Iterating over a time window to verify OTPs
        for i in range(window + 1):
            # Converting the counter to bytes
            counter_bytes = (counter - i).to_bytes(8, byteorder='big')

            # Converting the secret key to bytes
            secret_key_bytes = self.secret_key.encode('utf-8')

            # Using HMAC-SHA256 for hashing
            hmac_digest = hashlib.sha256(secret_key_bytes + counter_bytes).digest()

            # Extracting the dynamic truncation offset from the last 4 bits of the digest
            offset = hmac_digest[-1] & 0x0F

            # Extracting a 4-byte dynamic binary code from the digest
            binary_code = hmac_digest[offset:offset + 4]

            # Converting the binary code to an integer and format to be 6 digits
            calculated_otp = int.from_bytes(binary_code, byteorder='big') % 10**6
            calculated_otp_str = f'{calculated_otp:06d}'

            # Check if the calculated OTP matches the user-provided OTP
            if calculated_otp_str == user_otp:
                return True

        return False
