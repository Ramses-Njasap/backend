from django.urls import path
from properties.views.rooms import (
    PartitionAPIView, PartitionDetailAPIView,
    RoomPartitionAPIView, RoomPartitionDetailAPIView
)

app_name = 'rooms'
urlpatterns = [
    path('', PartitionAPIView.as_view(), name='partition-all'),
    path(
        '<int:pk>/', PartitionDetailAPIView.as_view(),
        name='partition-detail'
    ),
    path('', RoomPartitionAPIView.as_view(), name='rooms-all'),
    path(
        '<int:pk>/', RoomPartitionDetailAPIView.as_view(),
        name='rooms-detail'
    ),
]
