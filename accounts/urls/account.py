from accounts.views.account import VerificationView

from django.urls import path, include

app_name = 'account'
urlpatterns = [
    path("", VerificationView.as_view(), name="verifications"),
    path("auth/", include("accounts.urls.actions"))
]