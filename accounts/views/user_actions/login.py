# Import Django
from django.db import models
from django.conf import settings
from django.utils import timezone

# Import necessary libraries and modules from rest_framework
from rest_framework.response import Response
from rest_framework import status

# Import models from accounts models
from accounts.models.users import User
from accounts.models.account import LoginOTP

# Import serializers from accounts serializer
from accounts.serializers.login import LoginCredentialSerializer
from accounts.serializers.users import UserSerializer

from accounts.models.devices import DeviceToken, Device, DeviceLoginHistory

from utilities.generators.tokens import UserAuthToken, DeviceAuthenticator
from utilities.account import OTP as _OTP, Verification
from utilities.analysis.device_analysis import MatchDeviceAnalysis
from utilities import response

import threading
import requests
import base64
from security import safe_requests


class HandleLoginData:
    def __init__(self, with_code: bool = False):
        self.with_code = with_code

    def get_device_access_token(self, request, user_instance):
        if "Device-Authorization" in request.headers:
            header_values = request.headers["Device-Authorization"]

            try:
                header_values = header_values.split(" ")
                access_token = header_values[1]
            except Exception as e:
                response.errors(
                    field_error="Login Failed",
                    for_developer=(f"""Login Failed: Failed To Load
                                   Device Access Token: {str(e)}"""),
                    code="INTERNAL_SERVER_ERROR",
                    status_code=1011,
                    main_thread=False,
                    param=user_instance.pk
                )

            return access_token
        else:
            return None

    def get_active_device_instance(self, request, user_instance):
        access_token = self.get_device_access_token(request=request)

        if access_token:
            try:
                device_token_instance = DeviceToken.objects.get(
                    access_token=access_token)
            except DeviceToken.DoesNotExist:
                response.errors(
                    field_error="Login Failed",
                    for_developer=("Login Failed: Device Token Does Not Exist."
                                   " It Might Have Been Deleted During"
                                   " This Process By An External Request"),
                    code="INTERNAL_SERVER_ERROR",
                    status_code=1011,
                    main_thread=False,
                    param=user_instance.pk
                )
            except Exception as e:
                response.errors(
                    field_error="Login Failed",
                    for_developer=f"Login Failed: {str(e)}",
                    code="INTERNAL_SERVER_ERROR",
                    status_code=1011,
                    main_thread=False,
                    param=user_instance.pk
                )

            try:
                device_instance = Device.objects.get(tokens=device_token_instance)
            except Device.DoesNotExist:
                response.errors(
                    field_error="Logout Failed",
                    for_developer=("Device Does Not Exist."
                                   " It Might Have Been Deleted During"
                                   " This Process By An External Request"),
                    code="INTERNAL_SERVER_ERROR",
                    status_code=1011,
                    main_thread=False,
                    param=user_instance.pk
                )
            except Exception as e:
                response.errors(
                    field_error="Failed To Logout",
                    for_developer=f"Failed To Logout: {str(e)}",
                    code="INTERNAL_SERVER_ERROR",
                    status_code=1011,
                    main_thread=False,
                    param=user_instance.pk
                )

            return device_instance

        else:
            try:
                device_instance = Device.objects.create(
                    user=user_instance,
                    device_type=request.device_meta_info["device_type"],
                    client_type=request.device_meta_info["client_clientversion"],
                    operating_system=request.device_meta_info["os_osversion"],
                    _is_trusted=100)

            except Exception as e:
                response.errors(
                    field_error="Failure To Record Device",
                    for_developer=f"{str(e)}",
                    code="SERVER_ERROR",
                    status_code=1011,
                    main_thread=False,
                    param=user_instance.pk
                )

            return device_instance

    def set_device_login_history(self, request, user_ip,
                                 geolocation_data, user_instance):

        device_instance = self.get_active_device_instance(request=request)

        try:
            DeviceLoginHistory.objects.create(
                device=device_instance, ip_address=user_ip,
                physical_address=geolocation_data)

        except Exception as e:
            response.errors(
                field_error="Login Failed",
                for_developer=f"Login Failed: {str(e)}",
                code="INTERNAL_SERVER_ERROR",
                status_code=1011,
                main_thread=False,
                param=user_instance.pk
            )

    def get_geolocation(self, request, user_ip, callback, user_instance):

        try:
            # Perform the geolocation lookup
            url = f"https://ipinfo.io/{user_ip}/json/"
            res = safe_requests.get(url)
            geolocation_data = res.json()
            callback(request=request, geolocation_data=geolocation_data,
                     user_ip=user_ip, user_instance=user_instance)

        # This Error Response Should Use Websocket (Real Time)
        except requests.RequestException as e:
            response.errors(
                field_error="Failure To Get Device GeoLocation Data",
                for_developer=f"{str(e)}",
                code="SERVER_ERROR",
                status_code=1011,
                main_thread=False,
                param=user_instance.pk
            )

        except Exception as e:
            response.errors(
                field_error="Failure To Get Device GeoLocation Data",
                for_developer=f"{str(e)}",
                code="INTERNAL_SERVER_ERROR",
                status_code=1011,
                main_thread=False,
                param=user_instance.pk
            )

    def handle_geolocation(self, request, geolocation_data, user_ip, user_instance):

        self.set_device_login_history(request=request, user_ip=user_ip,
                                      geolocation_data=geolocation_data,
                                      user_instance=user_instance)

        return not None


# Login view class that extends from APIView
class Login:

    def __init__(self, request):
        self.request = request

    def check_remember_me_instance(self, remember_me):
        if not isinstance(remember_me, bool):
            response.errors(
                field_error="`remember_me` Field Must Be Boolean",
                for_developer="`remember_me` Field Must Be Boolean",
                code="BAD_REQUEST",
                status_code=400
            )

        return

    def get_query_id(self, user_instance):
        # Assuming that `user_instance.query_id` contains the binary data
        binary_data = user_instance.query_id
        if binary_data:
            # Encode the binary data to Base64
            return base64.b64encode(binary_data).decode('utf-8')
        return None

    # Handle HTTP Post method
    def login(self):

        remember_me = self.request.data.pop("remember_me", False)

        self.check_remember_me_instance(remember_me=remember_me)

        # Create user serializer instance using
        # request data and parsing request
        # to serializer class for extra functionality on request
        serializer = LoginCredentialSerializer(
            data=self.request.data, context={"request": self.request})

        # Validating is request body (data is valid)
        if serializer.is_valid():

            user_instance = serializer.validated_data['user']

            # Instantiating UserAuthToken
            auth_tokens = UserAuthToken(user=user_instance)

            # Getting access token and refresh token along side
            # their expiration times in seconds
            access, refresh = auth_tokens.get_token_pair()

            # Perform geolocation lookup asynchronously
            user_ip = self.request.device_meta_info["ip"]

            # Perform geolocation lookup in a separate thread
            geolocation_thread = threading.Thread(
                target=HandleLoginData().get_geolocation,
                args=(
                    self.request,
                    user_ip,
                    HandleLoginData().handle_geolocation,
                    user_instance,
                )
            )

            geolocation_thread.start()

            tokens_data = {
                "access": {
                    "token": access[0],
                    "exp": access[1].isoformat()
                },
                "refresh": {
                    "token": refresh[0],
                    "exp": refresh[1].isoformat()
                },
            }

            data = {}
            data["user"] = {}
            data["user"]["query_id"] = UserSerializer().get_query_id(user_instance)

            data["user"]["storage"] = {}

            data["user"]["storage"]["local"] = remember_me
            data["user"]["storage"]["session"] = not remember_me

            data["user"]["tokens"] = tokens_data

            return Response(data, status=status.HTTP_200_OK)

        # serializer_errors = response.serializer_errors(serializer.errors)

        # If the data is not valid, return validation errors
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginWithCode:

    def __init__(self, request):
        self.request = request

    def check_remember_me_instance(self, remember_me):
        if not isinstance(remember_me, bool):
            response.errors(
                field_error="`remember_me` Field Must Be Boolean",
                for_developer="`remember_me` Field Must Be Boolean",
                code="BAD_REQUEST",
                status_code=400
            )

        return

    def check_verification_validity(self, otp: str, user_instance: User,
                                    database_actions: bool = False,
                                    send_update: bool = False) -> bool:

        _otp_instance = _OTP(otp=otp, user=user_instance,
                             model=LoginOTP, database_actions=database_actions,
                             send_update=send_update)

        is_otp_valid = _otp_instance.is_valid()

        if is_otp_valid:
            return True

        response.errors(
            field_error="OTP VERIFICATION ERROR: Please Contact Support.",
            for_developer=f"An Error Occured In {self.__class__.__name__}.",
            code="INTERNAL_SERVER_ERROR",
            status_code=500
        )

    def get_user_from_request_data(self, request_data):
        email_or_phone = request_data["email_or_phone"]

        # Check if the input is an email or a phone number
        user_instance = User.objects.filter(
            models.Q(email=email_or_phone) | models.Q(phone=email_or_phone)
        ).first()

        return user_instance

    def login(self):

        remember_me = self.request.data.pop("remember_me", False)

        self.check_remember_me_instance(remember_me=remember_me)

        action = self.request.GET.get("action", None)

        # if not action:
        #     response.errors(
        #         field_error = "Login Error: Contact Support.",
        #         for_developer = "Login Error: Can't Determine What Action To Take.",
        #         code = "BAD_REQUEST",
        #         status_code = 400
        #     )

        user_instance = self.get_user_from_request_data(
            request_data=self.request.data)

        if user_instance is None:
            response.errors(
                field_error="Failed To Login: Wrong Login Credentials.",
                for_developer=(f"""Failed To Login: The Credentials
                                 {self.request.data['email_or_phone']}
                                 Didn't Match Any User."""),
                code="NOT_FOUND",
                status_code=404
            )

        if action and action.lower() == "retry":
            # Generate New Code And Send
            try:
                login_otp_instance = LoginOTP.objects.get(user=user_instance)
            except (LoginOTP.DoesNotExist, Exception):
                response.errors(
                    field_error=("OTP REQUEST ERROR:"
                                 " No OTP Was Found For This User."),
                    for_developer=("OTP REQUEST ERROR:"
                                   " No OTP Was Found For This User."),
                    code="NOT_FOUND",
                    status_code=404
                )

            if login_otp_instance.current_otp is None:
                response.errors(
                    field_error="ERROR: Please Request For OTP.",
                    for_developer=("ERROR: OTP Was Not Generated."
                                   " Try Requesting For OTP."),
                    code="NOT_FOUND",
                    status_code=404
                )

            # Check Login OTP Expiration

            # Compare Current Date Against OTP Creation Date
            date_diff = timezone.now() - login_otp_instance.updated_at

            otp_lifetime = settings.APPLICATION_SETTINGS["OTP_LIFETIME"]

            if date_diff.seconds > otp_lifetime.seconds:
                login_otp_instance.current_otp = None
                login_otp_instance.save()
                response.errors(
                    field_error="INVALID OTP: OTP EXPIRED",
                    for_developer=("INVALID OTP: OTP EXPIRED,"
                                   " REQUEST FOR NEW ONE"),
                    code="REQUEST_TIMEOUT",
                    status_code=408
                )

            otp = login_otp_instance.current_otp.otp

            self.check_verification_validity(
                user_instance=user_instance, otp=otp)

            # Creating a thread for the appropriate verification method
            try:
                send_verification_thread = threading.Thread(
                    target=getattr(
                        Verification(
                            user=user_instance, model=LoginOTP
                        ),
                        self.request.data["send_code_to"]
                    )
                )
                send_verification_thread.start()
            except Exception as e:
                response.errors(
                    field_error="Failure To Send OTP",
                    for_developer=f"{str(e)}",
                    code="SERVER_ERROR",
                    status_code=1011,
                    main_thread=False,
                    param=user_instance.pk
                )

            return Response(status=status.HTTP_200_OK)

        else:
            self.check_verification_validity(
                user_instance=user_instance, otp=self.request.data["otp"],
                database_actions=True, send_update=False)

            # Instantiating UserAuthToken
            auth_tokens = UserAuthToken(user=user_instance)

            # Getting access token and refresh token along side
            # their expiration times in seconds
            access, refresh = auth_tokens.get_token_pair()

            # Perform geolocation lookup asynchronously
            user_ip = self.request.device_meta_info["ip"]

            # Perform geolocation lookup in a separate thread
            geolocation_thread = threading.Thread(
                target=HandleLoginData(with_code=True).get_geolocation,
                args=(
                    self.request, user_ip,
                    HandleLoginData(with_code=True).handle_geolocation,
                    user_instance
                )
            )

            geolocation_thread.start()

            tokens_data = {
                "access": {
                    "token": access[0],
                    "exp": access[1].isoformat()
                },
                "refresh": {
                    "token": refresh[0],
                    "exp": refresh[1].isoformat()
                },
            }

            data = {}
            data["user"] = {}
            data["user"]["query_id"] = UserSerializer().get_query_id(user_instance)

            data["user"]["storage"] = {}

            data["user"]["storage"]["local"] = remember_me
            data["user"]["storage"]["session"] = not remember_me

            data["user"]["tokens"] = tokens_data

            return Response(data, status=status.HTTP_200_OK)


class LoginWithoutDeviceToken:

    def __init__(self, request):
        self.request = request

    def check_remember_me_instance(self, remember_me):
        if not isinstance(remember_me, bool):
            response.errors(
                field_error="`remember_me` Field Must Be Boolean",
                for_developer="`remember_me` Field Must Be Boolean",
                code="BAD_REQUEST",
                status_code=400
            )

        return

    def get_user_device_instances(self,
                                  user_instance: models.Model) -> models.QuerySet:
        """
        Retrieve all devices associated with the user.
        """
        return Device.objects.filter(user=user_instance)

    def login(self):
        remember_me = self.request.data.pop("remember_me", False)

        self.check_remember_me_instance(remember_me=remember_me)

        # Create user serializer instance using
        # request data and parsing request
        # to serializer class for extra functionality on request
        serializer = LoginCredentialSerializer(
            data=self.request.data, context={"request": self.request})

        # Validating is request body (data is valid)
        if serializer.is_valid():
            user_instance = serializer.validated_data['user']

            devices = self.get_user_device_instances(user_instance=user_instance)

            most_similar_device = MatchDeviceAnalysis(
                devices=devices, request=self.request).most_similar()

            # Instantiating UserAuthToken
            auth_tokens = UserAuthToken(user=user_instance)

            # Getting access token and refresh token along side
            # their expiration times in seconds
            access, refresh = auth_tokens.get_token_pair()

            tokens_data = {
                "access": {
                    "token": access[0],
                    "exp": access[1].isoformat()
                },
                "refresh": {
                    "token": refresh[0],
                    "exp": refresh[1].isoformat()
                },
            }

            data = {}

            # Setting User Data
            data["user"] = {}
            data["user"]["query_id"] = user_instance["query_id"]
            data["user"]["tokens"] = tokens_data

            # Setting Device Data
            data["device"] = {}

            access, refresh = DeviceAuthenticator(
                instance=most_similar_device).generate_tokens(
                    is_old_device=True if most_similar_device else False)

            device_tokens_data = {
                "access": {
                    "token": access[0],
                    "exp": access[1].isoformat()
                },
                "refresh": {
                    "token": refresh[0],
                    "exp": refresh[1].isoformat()
                },
            }

            data["device"]["tokens"] = device_tokens_data

            # Setting Storage Data
            data["storage"] = {}

            data["storage"]["local"] = remember_me
            data["storage"]["session"] = not remember_me

        return Response(data, status=200)
