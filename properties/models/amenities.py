from django.db import models
from django.utils.translation import gettext_lazy as _


class Amenity(models.Model):
    name = models.CharField(
        _("Amenity Name"), max_length=150, null=False, blank=False
    )
    description = models.CharField(_("Amenity Description"))

    def __str__(self):
        return str(self.name)

    class Meta:
        verbose_name = 'Amenity'
        verbose_name_plural = 'Amenities'
