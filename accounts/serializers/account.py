from rest_framework import serializers

from accounts.models.account import PhoneNumberVerificationOTP, AccountVerification, KYCVerificationCheck


class PhoneVerificationOTPSerializer(serializers.ModelSerializer):
    class Meta:
        model = PhoneNumberVerificationOTP
        fields = ('user', 'current_otp')


class KYCVerificationCheckSerializer(serializers.ModelSerializer):
    class Meta:
        model = KYCVerificationCheck
        fields = ("user", "id_card_verified", "passport_verified", "driver_license_verified",
                  "real_estate_certifications")


class AccountVerificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccountVerification
        fields = ("user", "email_verified", "phone_number_verified", "kyc_verification_check",
                  "score", "created_on", "updated_on")
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation["kyc_verification_check"] = KYCVerificationCheckSerializer(instance.kyc_verification_check).data
        return representation