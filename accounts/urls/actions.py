from django.urls import path
from django.conf import settings

from accounts.views.actions import (RedirectLoginView,
                                    RedirectRefreshAccessTokenView,
                                    RedirectLogoutView, RequestLoginOTP)


app_name = "actions"
urlpatterns = [
    path(settings.APPLICATION_SETTINGS["LOGIN_URL"]["URL"],
         RedirectLoginView.as_view(), name="login"),

    path(settings.APPLICATION_SETTINGS["REQUEST_LOGIN_OTP"]["URL"],
         RequestLoginOTP.as_view(), name="request-login-otp"),

    path("logout/", RedirectLogoutView.as_view(), name="logout"),

    path("refresh-access-token/",
         RedirectRefreshAccessTokenView.as_view(), name="refresh_access_token"),
]
