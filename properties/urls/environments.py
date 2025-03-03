from django.urls import path
from properties.views.environments import (
    EnvironmentAPIView, EnvironmentDetailAPIView
)

app_name = 'environments'
urlpatterns = [
    path('', EnvironmentAPIView.as_view(), name='all'),
    path(
        '<int:pk>/', EnvironmentDetailAPIView.as_view(),
        name='detail'
    ),
]
