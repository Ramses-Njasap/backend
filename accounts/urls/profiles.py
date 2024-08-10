from django.urls import path
from accounts.views.profiles import UserProfileView, UserProfileDetailView

app_name = 'profiles'
urlpatterns = [
    path('', UserProfileView.as_view(), name='users'),
    path('<str:query_id>/', UserProfileDetailView.as_view(), name='details')
]