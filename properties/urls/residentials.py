from django.urls import path
from properties.views.residentials import (
    ResidentialPropertyAPIView, ResidentialPropertyDetailAPIView
)

app_name = 'residentials'
urlpatterns = [
    path('', ResidentialPropertyAPIView.as_view(), name='all'),
    path(
        '<int:pk>/', ResidentialPropertyDetailAPIView.as_view(),
        name='detail'
    ),
]
