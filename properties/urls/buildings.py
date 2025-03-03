from django.urls import path
from properties.views.buildings import (
    BuildingAPIView
)

app_name = 'buildings'
urlpatterns = [
    path('', BuildingAPIView.as_view(), name='all'),
]
