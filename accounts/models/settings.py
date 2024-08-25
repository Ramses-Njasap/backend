from django.db import models
from accounts.models.users import User
from configurations.models.currencies import Currencies
from configurations.models.languages import Languages

class UserSettings(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=False, blank=False)
    preferred_currency = models.ForeignKey(Currencies, on_delete=models.DO_NOTHING)
    preferred_language = models.ForeignKey(Languages, on_delete=models.DO_NOTHING)

    def save(self, *args, **kwargs):
        if not self.preferred_currency:
            try:
                self.preferred_currency = Currencies.objects.get(code='USD'.upper())
            except Currencies.DoesNotExist:
                self.preferred_currency = Currencies.objects.create(
                    name='US Dollar', code='USD'.upper(), symbol='$'
                )
        
        if not self.preferred_language:
            try:
                self.preferred_language = Languages.objects.get(code='EN'.lower())
            except Languages.DoesNotExist:
                self.preferred_language =  Languages.objects.create(
                    name='English', code='EN'.lower(), flag='🇬🇧'
                )

        super().save(*args, **kwargs)