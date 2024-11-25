from django.db import models
from django.contrib.gis.db import models
from django.utils.translation import gettext_lazy as _


class Land(models.Model):
    # ref_id = models.CharField(_("Reference Identity"), max_length=100)
    latitude = models.FloatField(_("Latitude"))
    longitude = models.FloatField(_("Longitude"))

    boundary = models.PolygonField()

    class Meta:
        verbose_name_plural = 'Boundaries'