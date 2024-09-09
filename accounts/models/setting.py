from django.db import models
from accounts.models.auth import AuthCredential
from configurations.models.currency import Currency
from configurations.models.language import Language

class UserSetting(models.Model):
    user = models.OneToOneField(AuthCredential, on_delete=models.CASCADE, null=False, blank=False)
    preferred_currency = models.ForeignKey(Currency, on_delete=models.DO_NOTHING)
    preferred_language = models.ForeignKey(Language, on_delete=models.DO_NOTHING)