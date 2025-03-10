"""
URL configuration for LaLouge project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from utilities.views.sample import sample_view

# Base URL patterns
urlpatterns = [
    path('admin/', admin.site.urls),
]

# Account-related URL patterns
accounts_urlpatterns = [
    path('api/users/', include('accounts.urls.users')),
    path('api/account/', include('accounts.urls.account')),
    path('api/plans/', include('accounts.urls.plans', namespace='plans')),
    path(
        settings.APPLICATION_SETTINGS["LOGIN_URL"]["BASE"],
        include('accounts.urls.actions', namespace='actions'),
    ),
    path('sample-url/', sample_view, name='sample-view'),
]

properties_urlpatterns = [
    path(
        'api/properties/amenities/',
        include('properties.urls.amenities', namespace='amenities')
    ),
    path(
        'api/properties/buildings/',
        include('properties.urls.buildings', namespace='buildings')
    ),
    path(
        'api/properties/environments/',
        include('properties.urls.environments', namespace='environments')
    ),
    path(
        'api/properties/lands/',
        include('properties.urls.lands', namespace='lands')
    ),
    path(
        'api/properties/profiles/',
        include('properties.urls.profiles', namespace='profiles')
    ),
    path(
        'api/properties/residentials/',
        include('properties.urls.residentials', namespace='residentials')
    ),
    path(
        'api/properties/rooms/',
        include('properties.urls.rooms', namespace='rooms')
    ),
    path(
        'api/properties/units/',
        include('properties.urls.units', namespace='units')
    ),
]

# Static file URL patterns
static_urlpatterns = (
    static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
)

# Combine all patterns
urlpatterns += (
    accounts_urlpatterns + properties_urlpatterns
    + static_urlpatterns
)
