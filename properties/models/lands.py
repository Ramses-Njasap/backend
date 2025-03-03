from django.contrib.gis.db import models

from properties.models.environments import Environment


class LandProperty(models.Model):
    environment = models.OneToOneField(
        Environment, on_delete=models.CASCADE,
        null=False, blank=False
    )

    class Meta:
        verbose_name = 'Land Property'
        verbose_name_plural = 'Land Properties'
