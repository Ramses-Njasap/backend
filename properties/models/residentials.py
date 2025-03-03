from django.contrib.gis.db import models

from properties.models.buildings import Building
from properties.models.amenities import Amenity
from properties.models.environments import Environment


class ResidentialPropertyType(models.Model):
    name = models.CharField(max_length=100,
                            help_text=('Property type name. '
                                       'e.g Guest house, villa, '
                                       'apartment etc.'))

    def __str__(self):
        return f'{self.name}'


class ResidentialPropertyTypeInclusive(models.Model):
    main = models.OneToOneField(ResidentialPropertyType, on_delete=models.CASCADE,
                                help_text=('Main property type that includes '
                                           'other types. E.g: Villa can have '
                                           'apartments, guest houses'),
                                null=False, blank=False,
                                related_name='inclusive_main')
    includes = models.ManyToManyField(
        ResidentialPropertyType, related_name='inclusive_include')

    def __str__(self):
        includes = ", ".join(str(name) for name in self.includes.all())
        return f'{self.main} includes {includes}'


class ResidentialProperty(models.Model):

    environment = models.OneToOneField(
        Environment, on_delete=models.CASCADE,
        null=False, blank=False
    )
    _type = models.ForeignKey(
        ResidentialPropertyType, on_delete=models.CASCADE
    )
    buildings = models.ManyToManyField(Building)

    built_on = models.DateField()

    general_amenities = models.ManyToManyField(Amenity)

    partial_upload = models.BooleanField(default=False)

    query_id = models.BinaryField(
        null=False, blank=False, max_length=10000, db_index=True
    )

    class Meta:
        verbose_name = 'Residential Property'
        verbose_name_plural = 'Residential Properties'
