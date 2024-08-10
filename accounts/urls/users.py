from django.urls import path, include
from accounts.views.users import UserAPIView

app_name = 'users'
urlpatterns = [
    path('', UserAPIView.as_view(), name='users'),
    path('profiles/', include('accounts.urls.profiles')),
]