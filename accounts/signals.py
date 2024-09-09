from django.db.models.signals import post_save
from django.db import transaction
from django.apps import apps
from django.dispatch import receiver

from accounts.models.setting import UserSetting
from accounts.models.mlm_user import MLMUser
from accounts.models.profiles import UserProfile
from accounts.models.devices import DeviceWallet
from accounts.models.account import (AccountVerification, KYCVerificationCheck, RealEstateCertification)

from configurations.models.currency import Currency
from configurations.models.language import Language
from utilities.generators.tokens import DeviceAuthenticator


@receiver(post_save, sender=apps.get_model('accounts', 'AuthCredential'))
def create_profile_and_referral(sender, instance, created, **kwargs):
    """
    Signal handler to create a UserProfile and Referral instance for a new user.
    """
    if created:
        user_setting = UserSetting(user=instance)

        """
        Wrapping the code in transaction.atomic() ensures that either both the currency and language are set correctly or neither are, preventing partial updates.
        """
        with transaction.atomic():
            # Get or create the preferred currency
            # By default, users should use Us Dollar
            usd_currency, created = Currency.objects.get_or_create(
                code='USD',
                defaults={'name': 'US Dollar', 'symbol': '$'}
            )
            user_setting.preferred_currency = usd_currency

            # Get or create the preferred language
            # By default, users should use British English
            english_language, created = Language.objects.get_or_create(
                code='EN',
                defaults={'name': 'English', 'flag': '🇬🇧'}
            )
            user_setting.preferred_language = english_language

        user_setting.save()

        UserProfile.objects.create(user=instance)
        real_estate_certifications_instance = RealEstateCertification.objects.create(user=instance)
        kyc_verification_check_instance = KYCVerificationCheck.objects.create(user=instance,
                                                                        real_estate_certifications=real_estate_certifications_instance)
        AccountVerification.objects.create(user=instance, kyc_verification_check=kyc_verification_check_instance)

        if instance.is_mlm_user:
            MLMUser.objects.create(user=instance)


@receiver(post_save, sender=apps.get_model('accounts', 'Device'))
def create_user_device(sender, instance, created, **kwargs):
    """
    Signal to handle creation of device tokens, wallets and device history upon creation of Device
    """

    if created:

        # Creating Device Wallet
        device_wallet_instance = DeviceWallet.objects.create(
                                        synced_amount=(0).to_bytes(8, byteorder='big', signed=True),
                                        amount_in_sync_transition=(0).to_bytes(8, byteorder='big', signed=True),
                                        unsynced_amount=(0).to_bytes(8, byteorder='big', signed=True)
                                    )
        
        instance.wallet = device_wallet_instance

        # Creating Device Tokens
        DeviceAuthenticator(instance=instance, database_actions=True).generate_tokens()