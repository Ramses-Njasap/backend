from django.urls import path
from properties.views.lands import (
    LandPropertyAPIView, LandPropertyDetailAPIView
)

app_name = 'lands'
urlpatterns = [
    path('', LandPropertyAPIView.as_view(), name='all'),
    path(
        '<int:pk>/', LandPropertyDetailAPIView.as_view(),
        name='detail'
    ),
]
