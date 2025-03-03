from django.db import models
from django.conf import settings

from accounts.models.users import User

from configurations.models.currencies import Currencies
from configurations.models.languages import Languages

application_setting = settings.APPLICATION_SETTINGS
default_currency = application_setting["DEFAULT_CURRENCY"]
default_language = application_setting["DEFAULT_LANGUAGE"]


class UserSettings(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, null=False, blank=False
    )
    preferred_currency = models.ForeignKey(Currencies, on_delete=models.DO_NOTHING)
    preferred_language = models.ForeignKey(Languages, on_delete=models.DO_NOTHING)

    def save(self, *args, **kwargs):
        if not self.pk:
            # Use get_or_create for preferred_currency
            self.preferred_currency, _ = Currencies.objects.get_or_create(
                code=(
                    default_currency["code"]
                    if default_currency["code"]
                    else "USD"
                ),
                defaults={
                    "name": (
                        default_currency["name"]
                        if default_currency["name"]
                        else "US Dollar"
                    ),
                    'symbol': (
                        default_currency["symbol"]
                        if default_currency["symbol"]
                        else "$"
                    )
                }
            )

            # Use get_or_create for preferred_language
            self.preferred_language, _ = Languages.objects.get_or_create(
                code=(
                    default_language["code"]
                    if default_language["code"]
                    else "en"
                ),
                defaults={
                    "name": (
                        default_language["name"]
                        if default_language["name"]
                        else "English"
                    ),
                    "flag": (
                        default_language["flag"]
                        if default_language["flag"]
                        else "🇬🇧"
                    )
                }
            )

        # Call the original save method
        super().save(*args, **kwargs)
