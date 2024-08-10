from django.db import models

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import JSONParser

from utilities.models.fields import validation
from utilities.generators.otp import OTPGenerator
from utilities.permissions import DeviceAuthPermission
from utilities.permissions import GrantPermission
from utilities.account import Verification
from utilities.generators.string_generators import QueryID
from utilities import response

# Importing `models` Modules From Package `accounts.models`
from accounts.models.users import User
from accounts.models.account import LoginOTP
from accounts.models.devices import Device, DeviceLoginHistory

from accounts.views.client_actions.login import Login as ClientLogin
from accounts.views.user_actions.login import Login as UserLogin, LoginWithCode as UserLoginWithCode, LoginWithoutDeviceToken
from accounts.views.client_actions.refresh_access_token import RefreshAccessToken as ClientRefreshAccessToken
from accounts.views.user_actions.refresh_access_token import RefreshAccessToken as UserRefreshAccessToken
from accounts.views.client_actions.logout import Logout as ClientLogout
from accounts.views.user_actions.logout import Logout as UserLogout

from difflib import SequenceMatcher

import threading, requests


class RedirectLoginView(APIView):

    parser_classes = (JSONParser,)

    def check_device_authorization_header(self):
        if "Device-Authorization" not in self.request.headers:
            return False
        return True

    def get_permissions(self):
        is_device_auth_header_exists = self.check_device_authorization_header()

        if not is_device_auth_header_exists:
            return []
        
        if not self.request.GET.get("login-with"):
            return [DeviceAuthPermission()]
        else:
            login_with = self.request.GET.get("login-with")
            if login_with.lower() != "code":
                return [DeviceAuthPermission()]
            else:
                return []

    def post(self, request):

        # is_device_auth_header_exists = self.check_device_authorization_header()

        # if not is_device_auth_header_exists:
        #     user_instance = None
        #     # Perform geolocation lookup asynchronously
        #     user_ip = request.device_meta_info["ip"]
            
        #     # Perform geolocation lookup in a separate thread
        #     geolocation_thread = threading.Thread(target=self.get_geolocation, args=(request.device_meta_info, user_ip, self.handle_geolocation, user_instance))
        #     geolocation_thread.start()

        request_by = self.request.GET.get("requested-by", None)
        login_with = self.request.GET.get('login-with', None)

        if self.request.GET.get("test"):
            return LoginWithoutDeviceToken(request=request).login()
        
        if request_by:
            if request_by.lower() == 'user':
                if login_with and login_with.lower() == "code":
                    login_view = UserLoginWithCode(request=request)
                else:
                    login_view = UserLogin(request=request)

            elif request_by.lower() == 'client':
                login_view = ClientLogin(request=request)

            else:
                return Response(status=status.HTTP_400_BAD_REQUEST)

            return login_view.login()
        
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)


class RedirectRefreshAccessTokenView(APIView):

    def post(self, request):
        request_by = self.request.GET.get("requested-by", None)
        
        if request_by:
            if request_by.lower() == 'user':
                login_view = UserRefreshAccessToken.as_view()

            elif request_by.lower() == 'client':
                login_view = ClientRefreshAccessToken.as_view()

            else:
                return Response(status=status.HTTP_400_BAD_REQUEST)
            
            # Extracting the HttpRequest object from the DRF Request object
            http_request = request._request

            # login_view_instance = login_view()
            return login_view(http_request)
        
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)


class RedirectLogoutView(APIView):

    permission_classes = (GrantPermission,)

    def post(self, request, *args, **kwargs):
        request_by = self.request.GET.get("requested-by", None)
        
        if request_by:
            if request_by.lower() == 'user':
                logout_view = UserLogout(request)

            elif request_by.lower() == 'client':
                logout_view = ClientLogout(request)

            else:
                return Response(status=status.HTTP_400_BAD_REQUEST)
            
            return logout_view.logout()
        
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)


class RequestLoginOTP(APIView):
    
    def get_permissions(self):
        # Applying Different Permission Classes Based On URL Query
        if self.request.GET.get("active-user"):
            return [DeviceAuthPermission()]
        
        return []

    def get_user_instance(self, email_or_phone: str):

        # Checking if the input is an email or a phone number
        user_instance = User.objects.filter(
            models.Q(email=email_or_phone) | models.Q(phone=email_or_phone)
        ).first()

        return user_instance

    def post(self, request):
        email_or_phone = request.data["email_or_phone"]

        if not email_or_phone:
            response.errors(
                field_error="Email Or Phone Value Not Found.",
                for_developer="Email Or Phone Value Not Found.",
                code="BAD_REQUEST",
                status_code=400
            )

        user_instance = self.get_user_instance(email_or_phone=email_or_phone)

        if not user_instance:
            response.errors(
                field_error="User Error: Couldn't Find User With The Inputted Credentials.",
                for_developer=f"User Error: Couldn't Find User With The Inputted Credentials ({email_or_phone}).",
                code="NOT_FOUND",
                status_code=404
            )
        
        otp = OTPGenerator(secret_key=user_instance.get_secret_key, model=LoginOTP, user=user_instance)
        otp.generate_otp()

        # Determining the verification type
        verification_type = "email" if user_instance.email else "phone"

        # Creating a thread for the appropriate verification method
        send_verification_thread = threading.Thread(
            target=getattr(Verification(user=user_instance, model=LoginOTP), verification_type)
        )
        send_verification_thread.start()

        return Response(status=status.HTTP_200_OK)


class ChangePasswordAPI(APIView):
    permission_classes = (GrantPermission,)

    def password_similarity(self, current_password: str, new_password: str) -> float:
        """
        Calculate similarity between old and new passwords.
        Returns a similarity score between 0 and 1.
        0 means completely different, 1 means identical.
        """
        # Normalize the strings to lowercase to ensure case insensitivity
        current_password = current_password.lower()
        new_password = new_password.lower()

        # Calculate similarity using SequenceMatcher
        similarity = SequenceMatcher(None, current_password, new_password).ratio()

        return similarity

    # Cannot use validate_password function name since it is already an inbuilt serializer function name
    # following the serializer validate function naming pattern validate_{field_name}
    def validate_user_password(self, value: str, user_instance: User = None):
        if user_instance:
            filtered_data = {key: value for key, value in user_instance.__dict__.items() if key != 'password'}

            validate_password = validation.PasswordValidation(value, filtered_data)
        
        else:
            validate_password = validation.PasswordValidation(value)

        # Check password validation
        password_validation = validate_password.validate_or_raise()

        return password_validation

    def post(self, request):

        current_password = request.data["current_password"]
        new_password = request.data["new_password"]

        if None in [current_password, new_password]:
            response.errors(
                field_error="Missing Field Error: Make Sure To Fill In Both Current And New Password.",
                for_developer="Missing Field Error: Make Sure To Fill In Both Current And New Password.",
                code="BAD_REQUEST",
                status_code=400
            )

        if request.user.check_password(current_password):

            similarity_score = self.password_similarity(current_password=current_password, new_password=new_password)

            if similarity_score < 0.6:
                response.errors(
                    field_error="New And Current Passwords Are Similar. Try With A Different Password.",
                    for_developer=f"Current And New Password Had A Similarity Ratio Of {similarity_score} Which Is Less Than 0.6.",
                    code="NOT_ACCEPTABLE",
                    status_code=406
                )
            
            validated_password = self.validate_user_password(value=current_password, user_instance=request.user)

            request.user.password = validated_password

            request.user.save()
        
        else:
            response.errors(
                field_error="Password Does Not Match Existing Password.",
                for_developer="Password Does Not Match Existing Password.",
                code="IM_A_TEAPOT",
                status_code=418
            )

        return Response(status=status.HTTP_200_OK)