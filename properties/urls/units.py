from django.urls import path
from properties.views.units import (
    UnitAPIView, UnitDetailAPIView
)

app_name = 'units'
urlpatterns = [
    path('', UnitAPIView.as_view(), name='all'),
    path(
        '<int:pk>/', UnitDetailAPIView.as_view(),
        name='detail'
    ),
]
