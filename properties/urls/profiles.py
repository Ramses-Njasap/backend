from django.urls import path
from properties.views.profiles import (
    ProfileAPIView, ProfileDetailAPIView
)

app_name = 'profiles'
urlpatterns = [
    path('', ProfileAPIView.as_view(), name='all'),
    path(
        '<int:pk>/', ProfileDetailAPIView.as_view(),
        name='detail'
    ),
]
