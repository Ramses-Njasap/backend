from django.contrib.gis.db import models


class Boundary(models.Model):
    boundary = models.PolygonField(
        # WGS84 link to
        # read: https://en.wikipedia.org/wiki/World_Geodetic_System
        srid=4326,
    )

    class Meta:
        verbose_name = 'Boundary'
        verbose_name_plural = 'Boundaries'
