from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from accounts.models.users import User

from utilities.generators.device import DeviceSignature


class DeviceTokenBlacklist(models.Model):
    access_token = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)

    # `updated_at` field is not really necessary in a perfectly secured system
    # But, since now system is perfectly secured, we will need it to monitor
    # if there's any change in `instance` values
    # Since there shouldn't be any change in this instances, any change will mean
    # there's an attack

    # If `updated_at` has any value, it means there's something wrong somewhere.
    updated_at = models.DateTimeField(auto_now=True)


class DeviceToken(models.Model):
    access_token = models.TextField()
    refresh_token = models.TextField()

    access_token_expires_at = models.DateTimeField()
    refresh_token_expires_at = models.DateTimeField()

    blacklisted_tokens = models.ManyToManyField("DeviceTokenBlacklist")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def is_refresh_token_expired(self):
        return timezone.now() > self.refresh_token_expires_at

    def is_access_token_expired(self):
        return timezone.now() > self.access_token_expires_at

    def token_blacklist(self):
        if self.is_access_token_expired():
            blacklisted_token_instance = DeviceTokenBlacklist.objects.create(
                access_token=self.access_token)

            self.blacklisted_tokens.add(blacklisted_token_instance)


class DeviceWallet(models.Model):
    synced_amount = models.BinaryField()
    amount_in_sync_transition = models.BinaryField()
    unsynced_amount = models.BinaryField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Device(models.Model):

    class DeviceType(models.TextChoices):
        MOBILE = "MOBILE", _("Mobile")
        PC = "PC", _("Pc")
        TABLET = "TABLET", _("Tablet")
        OTHER = "OTHER", _("Other")
        UNDEFINED = "UNDEFINED", _("Undefined")

    user = models.ForeignKey(User, on_delete=models.CASCADE)

    user_agent = models.TextField(null=True)

    device_name = models.CharField(max_length=150, default="")

    _device_token = models.TextField(null=True, blank=True)

    device_type = models.CharField(max_length=11, choices=DeviceType.choices,
                                   default=DeviceType.UNDEFINED)

    client_type = models.CharField(max_length=150, default=",")

    operating_system = models.CharField(max_length=60, default=",")

    device_signature = models.BinaryField(
        null=False, blank=False, max_length=10000)
    is_synced = models.BooleanField(default=True)

    # This records the percentage trust the system has for this device
    _is_trusted = models.PositiveSmallIntegerField(default=0)

    wallet = models.OneToOneField(
        DeviceWallet, null=True, blank=True,
        on_delete=models.SET_NULL)

    tokens = models.OneToOneField(
        DeviceToken, null=True, blank=True,
        on_delete=models.SET_NULL)

    # `refresh_token_renewal_count` field is for
    # the purpose of determinig Trust in a device.
    # If a device has successfully renewed its
    # refresh token 2 times with a max laps of 48 hours, that is:
    refresh_token_renewal_count = models.PositiveSmallIntegerField(
        default=0, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def sync_and_unsync_device(self):

        if self.is_synced:
            amount_in_sync_transition = self.wallet.amount_in_sync_transition

            if amount_in_sync_transition != 0:
                self.wallet.synced_amount -= amount_in_sync_transition

                self.wallet.save()
                self.is_synced = False
                self.save()

        else:
            self.wallet.synced_amount += self.wallet.unsynced_amount
            self.wallet.amount_in_sync_transition = self.wallet.unsynced_amount
            self.wallet.unsynced_amount = 0

            self.wallet.save()

            self.is_synced = True
            self.save()

    def assign_device_signature(self, data, length):

        device_signature_instance = DeviceSignature(data=data, length=length)

        # Generating device_signature and saving it to database
        self.device_signature = device_signature_instance.to_database()

        self.save()


class DeviceLoginHistory(models.Model):
    device = models.ForeignKey(Device, on_delete=models.CASCADE)
    ip_address = models.GenericIPAddressField(protocol='both')
    physical_address = models.JSONField()
    login_at = models.DateTimeField(auto_now_add=True)
    logout_at = models.DateTimeField(null=True)
