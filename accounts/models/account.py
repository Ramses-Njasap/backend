from django.db import models
from django.core.validators import (MaxValueValidator, MinValueValidator)

from utilities.conversions import String
from utilities.generators.string_generators import QueryID

import uuid


class OTP(models.Model):
    otp = models.CharField(max_length=6)
    created_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Phone Number Verification OTP"
        verbose_name_plural = "Phone Number Verification OTPs"


class LoginOTP(models.Model):
    user = models.OneToOneField('AuthCredential', on_delete=models.CASCADE)
    used_otp = models.ManyToManyField('OTP', through='UsedOTP', related_name='login_otp')
    current_otp = models.OneToOneField('OTP', on_delete=models.DO_NOTHING, null=True)
    updated_at = models.DateTimeField(auto_now=True)


class PhoneNumberVerificationOTP(models.Model):
    user = models.OneToOneField('AuthCredential', on_delete=models.CASCADE)
    used_otp = models.ManyToManyField('OTP', through='UsedOTP', related_name='phone_number_used_otp')
    current_otp = models.OneToOneField('OTP', on_delete=models.DO_NOTHING, null=True)
    updated_at = models.DateTimeField(auto_now=True)


class EmailVerificationOTP(models.Model):
    user = models.OneToOneField('AuthCredential', on_delete=models.CASCADE)
    used_otp = models.ManyToManyField('OTP', through='UsedOTP', related_name='email_used_otp')
    current_otp = models.OneToOneField('OTP', on_delete=models.DO_NOTHING, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Email Verification OTP"
        verbose_name_plural = "Email Verification OTPs"


class UsedOTP(models.Model):
    otp = models.ForeignKey('OTP', on_delete=models.CASCADE)
    phone_number_verification_otp = models.ForeignKey('PhoneNumberVerificationOTP', on_delete=models.SET_NULL, null=True)
    email_verification_otp = models.ForeignKey(EmailVerificationOTP, on_delete=models.SET_NULL, null=True)
    login_otp = models.ForeignKey(LoginOTP, on_delete=models.SET_NULL, null=True)
    is_active = models.BooleanField(default=True)
    used_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Used OTP"
        verbose_name_plural = "Used OTPs"


class OTPModels:
    phone = PhoneNumberVerificationOTP
    email = EmailVerificationOTP


class RealEstateCertification(models.Model):
    user = models.OneToOneField('AuthCredential', on_delete=models.CASCADE)


class KYCVerificationCheck(models.Model):

    class FieldScoreValue:
        ID_CARD_VERIFIED = 60
        PASSPORT_VERIFIED = 20
        DRIVER_LICENSE_VERIFIED = 20
        REAL_ESTATE_CERTIFICATIONS = 100

    user = models.OneToOneField('AuthCredential', on_delete=models.CASCADE)
    id_card_verified = models.BooleanField(default=False)
    passport_verified = models.BooleanField(default=False)
    driver_license_verified = models.BooleanField(default=False)
    real_estate_certifications = models.OneToOneField('RealEstateCertification', on_delete=models.DO_NOTHING, null=True, blank=True)

    class Meta:
        verbose_name = 'KYC Verification'
        verbose_name_plural = 'KYC Verifications'

    @property
    def get_score(self):
        total_score = 0
        for field in self._meta.fields:
            if field.name != 'real_estate_certifications':
                if isinstance(field, models.BooleanField):
                    field_value = getattr(self, field.name)

                    if field_value:
                        total_score += getattr(self.FieldScoreValue, field.name, 0)
        
        return total_score


class AccountVerification(models.Model):

    class FieldScoreValue:
        EMAIL_VERIFIED = 10
        PHONE_NUMBER_VERIFIED = 10
        KYC_VERIFICATION_CHECK = 80

    user = models.OneToOneField('AuthCredential', on_delete=models.CASCADE)
    email_verified = models.BooleanField(default=False)
    phone_number_verified = models.BooleanField(default=False)
    kyc_verification_check = models.OneToOneField('KYCVerificationCheck', on_delete=models.DO_NOTHING, null=True, blank=True)
    score = models.DecimalField(default=0, decimal_places=2, max_digits=5)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Account Verification'
        verbose_name_plural = 'Account Verifications'
        ordering = ['-score']

    
    """
    THIS PARTICULAR FUNCTION HARD ME. I GO CHECK'AM AFTER I DON GET SENSE
    """
    @property
    def get_score(self):
        total_score = 0

        # Iterate over all fields of the model
        for field in self._meta.fields:
            # Exclude the KYCVerificationCheck field
            if field.name != 'kyc_verification_check':
                # Check if the field is a BooleanField
                if isinstance(field, models.BooleanField):
                    # Get the field value (True/False)
                    field_value = getattr(self, field.name)
                    
                    # If the field is True, add its corresponding score
                    if field_value:
                        total_score += getattr(self.FieldScoreValue, field.name, 0)
        
        total_score += ((self.kyc_verification_check.get_score/200) * 80)

        return total_score

    def save(self, *args, **kwargs):
        # Updating the score before saving the model
        self.score = self.get_score

        super().save(*args, **kwargs)