from django.db import models


class Currencies(models.Model):
    name = models.CharField(max_length=100, null=False, blank=False)
    symbol = models.CharField(max_length=10, null=False, blank=False)
    code = models.CharField(max_length=3, unique=True, null=False, blank=False)

    class Meta:
        verbose_name = 'Currency'
        verbose_name_plural = 'Currencies'

    def __str__(self):
        return f"{self.name} {self.code}"