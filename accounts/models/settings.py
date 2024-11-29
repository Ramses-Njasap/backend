from django.db import models
from accounts.models.users import User
from configurations.models.currencies import Currencies
from configurations.models.languages import Languages


class UserSettings(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, null=False, blank=False)
    preferred_currency = models.ForeignKey(Currencies, on_delete=models.DO_NOTHING)
    preferred_language = models.ForeignKey(Languages, on_delete=models.DO_NOTHING)

    def save(self, *args, **kwargs):
        if not self.pk:
            # Use get_or_create for preferred_currency
            self.preferred_currency, _ = Currencies.objects.get_or_create(
                code='USD',
                defaults={'name': 'US Dollar', 'symbol': '$'}
            )

            # Use get_or_create for preferred_language
            self.preferred_language, _ = Languages.objects.get_or_create(
                code='en',  # Use lowercase 'en' here directly
                defaults={'name': 'English', 'flag': '🇬🇧'}
            )

        # Call the original save method
        super().save(*args, **kwargs)
