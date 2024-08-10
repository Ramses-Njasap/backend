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

urlpatterns = [
    path('admin/', admin.site.urls),
]

accounts_urlpatterns = [
    path('api/users/', include('accounts.urls.users')),
    path("api/account/", include("accounts.urls.account")),
    path('api/plans/', include("accounts.urls.plans", namespace="plans")),
    path(settings.APPLICATION_SETTINGS["LOGIN_URL"]["BASE"], include("accounts.urls.actions", namespace="actions")),
    path('sample-url/', sample_view, name='sample-view'),
]

# parsing static urls to static_urlpatterns
# this will be use to navigate through static contents (especially images) in the any browser
static_urlpatterns = static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

urlpatterns += accounts_urlpatterns + static_urlpatterns
