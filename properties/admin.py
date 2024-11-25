# from django.contrib import admin
from django.contrib.gis import admin
from properties.models.homes import Home
from properties.models.lands import Land
from properties.models.boundaries import Boundary

admin.site.register(Home)
admin.site.register(Land)


admin.register(Boundary)
