from django.contrib.gis.db import models


class Boundary(models.Model):
    boundary = models.PolygonField(srid=4326, # WGS84 link to read: https://en.wikipedia.org/wiki/World_Geodetic_System
                                   )
    
    class Meta:
        verbose_name = 'Boundary'
        verbose_name_plural = 'Boundaries'