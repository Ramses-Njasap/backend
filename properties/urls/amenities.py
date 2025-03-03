from django.urls import path
from properties.views.amenities import (
    AmenityAPIView, AmenityDetailAPIView
)

app_name = 'amenities'
urlpatterns = [
    path('', AmenityAPIView.as_view(), name='all'),
    path('<int:pk>/', AmenityDetailAPIView.as_view(), name='details')
]
