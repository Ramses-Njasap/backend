from django.db.models.signals import post_save
from django.apps import apps
from django.dispatch import receiver

from accounts.models.devices import DeviceWallet

from utilities.generators.tokens import DeviceAuthenticator


# @receiver(post_save, sender=apps.get_model('accounts', 'User'))
# def create_profile_and_referral(sender, instance, created, **kwargs):
#     """
#     Signal handler to create a UserProfile
#     and Referral instance for a new user.
#     """
#     if created:


@receiver(post_save, sender=apps.get_model('accounts', 'Device'))
def create_user_device(sender, instance, created, **kwargs):
    """
    Signal to handle creation of device tokens,
    wallets and device history upon creation of Device
    """

    if created:

        # Creating Device Wallet
        device_wallet_instance = DeviceWallet.objects.create(
            synced_amount=(0).to_bytes(8, byteorder='big', signed=True),
            amount_in_sync_transition=(0).to_bytes(8, byteorder='big', signed=True),
            unsynced_amount=(0).to_bytes(8, byteorder='big', signed=True))

        instance.wallet = device_wallet_instance

        # Creating Device Tokens
        DeviceAuthenticator(
            instance=instance, database_actions=True).generate_tokens()
