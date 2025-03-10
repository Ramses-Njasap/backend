from typing import List, Union
from django.conf import settings
from django.utils.timezone import now

# Import necessary libraries and modules from rest_framework
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

# Import models from accounts models
from accounts.models.users import User, APIKey
from accounts.models.devices import Device, DeviceLoginHistory
from accounts.models.settings import UserSettings
from accounts.models.mlm_user import MLMUser
from accounts.models.profiles import UserProfile
from accounts.models.account import (
    PhoneNumberVerificationOTP, EmailVerificationOTP, AccountVerification,
    KYCVerificationCheck, RealEstateCertification
)

# Import serializers from accounts serializer
from accounts.serializers.users import UserSerializer

from utilities import response
from utilities.account import Verification
from utilities.generators.string_generators import QueryID
from utilities.permissions import GrantPermission

from rest_framework.pagination import PageNumberPagination

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from datetime import timedelta

import time
import requests
import threading
import secrets


# Load Application Settings
app_settings = getattr(settings, "APPLICATION_SETTINGS", {})


class CustomPageNumberPagination(PageNumberPagination):
    page_size = 10  # Number of items per page
    page_size_query_param = 'page_size'
    max_page_size = 1


# User view class that extends from APIView
class UserAPIView(APIView):

    def get_permissions(self):
        if self.request.method == 'GET':
            return [GrantPermission()]
        return []

    pagination_class = CustomPageNumberPagination

    def check_remember_me_instance(self, remember_me):
        if not isinstance(remember_me, bool):
            response.errors(
                field_error="`remember_me` Field Must Be Boolean",
                for_developer="`remember_me` Field Must Be Boolean",
                code="BAD_REQUEST",
                status_code=400
            )

        return

    # Handle HTTP Post method
    def post(self, request):

        remember_me = request.data.pop("remember_me", False)

        self.check_remember_me_instance(remember_me=remember_me)

        # Create user serializer instance using
        # request data and parsing request
        # to serializer class for extra functionality on request
        serializer = UserSerializer(data=request.data, context={'request': request})

        # Validating is request body (data is valid)
        if serializer.is_valid():

            # Save the user instance to the database
            user_instance = serializer.save()

            user_instance._pk_hidden = False
            user_instance.save()

            # Perform geolocation lookup asynchronously
            user_ip = request.device_meta_info["ip"]

            # Perform geolocation lookup in a separate thread
            geolocation_thread = threading.Thread(
                target=self._completion,
                args=(request.device_meta_info, user_ip,
                      self.handle_geolocation, user_instance))

            geolocation_thread.start()

            # Determining the verification type
            if user_instance.email:
                verification_type = ["email", EmailVerificationOTP]
            else:
                verification_type = ["phone", PhoneNumberVerificationOTP]

            # Creating a thread for the appropriate verification method
            send_verification_thread = threading.Thread(
                target=getattr(
                    Verification(user=user_instance, model=verification_type[1]),
                    verification_type[0])
            )

            send_verification_thread.start()

            # Create the response data

            data = {}
            data["user"] = {}
            data["user"]["query_id"] = serializer.data["query_id"]

            data["user"]["storage"] = {}

            data["user"]["storage"]["local"] = remember_me
            data["user"]["storage"]["session"] = not remember_me

            return Response(data, status=status.HTTP_201_CREATED)

        # serializer_errors = response.serializer_errors(serializer.errors)

        # If the data is not valid, return validation errors
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def generate_api_key(
            self, user, name=None, expires_in_days=None, scopes=None
    ):
        """
        Generate and associate an API key with the user.

        Args:
            user: User instance.
            name (str): A name for the API key (optional).
            expires_in_days (int): Number of days until the key expires (optional).
            scopes (str): A comma-separated list of scopes (optional).

        Returns:
            APIKey: The created APIKey instance.
        """
        key = secrets.token_urlsafe(32)
        expires_at = None
        if expires_in_days:
            expires_at = now() + timedelta(days=expires_in_days)
        return APIKey.objects.create(
            user=user,
            key=key,
            name=name,
            expires_at=expires_at,
            scopes=scopes
        )

    def _user_completion(self, instance):
        if instance:
            UserProfile.objects.create(user=instance)

            UserSettings.objects.create(user=instance)

            real_estate_certifications_instance = (
                RealEstateCertification.objects.create(
                    user=instance
                )
            )

            kyc_verification_check_instance = (
                KYCVerificationCheck.objects.create(
                    user=instance,
                    real_estate_certifications=real_estate_certifications_instance
                )
            )

            AccountVerification.objects.create(
                user=instance,
                kyc_verification_check=kyc_verification_check_instance
            )

            if instance.is_mlm_user:
                MLMUser.objects.create(user=instance)

            # if user is external user
            if instance.user_type.lower() == instance.UserType.EXTERNAL.lower():
                self.generate_api_key(
                    user=instance,
                    expires_in_days=(
                        app_settings.get("API_KEY", {}).get("EXPIRES_IN", 14)
                    )
                )

    def _completion(self, device_meta_info, user_ip, callback, user_instance):
        try:
            self._user_completion(instance=user_instance)
        except Exception as e:
            response.errors(
                field_error="Failure To Get Device GeoLocation Data",
                for_developer=f"{str(e)}",
                code="SERVER_ERROR",
                status_code=1011,
                main_thread=False,
                param=user_instance.pk
            )

        try:
            # Perform the geolocation lookup
            url = f"https://ipinfo.io/{user_ip}/json/"
            res = requests.get(url)
            geolocation_data = res.json()
            callback(device_meta_info=device_meta_info,
                     geolocation_data=geolocation_data, user_ip=user_ip,
                     user_instance=user_instance)

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
                code="SERVER_ERROR",
                status_code=1011,
                main_thread=False,
                param=user_instance.pk
            )

    def handle_geolocation(self, device_meta_info, geolocation_data,
                           user_ip, user_instance):
        # Handle the geolocation data, save it to the database, etc.
        try:
            device_instance = Device.objects.create(
                user=user_instance,
                user_agent=str(device_meta_info["user_agent"]),
                device_type=device_meta_info["device_type"],
                client_type=device_meta_info["client_clientversion"],
                operating_system=device_meta_info["os_osversion"],
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

        try:
            DeviceLoginHistory.objects.create(
                device=device_instance, ip_address=user_ip,
                physical_address=geolocation_data)

        except Exception as e:
            response.errors(
                field_error="Failure To Record Login History.",
                for_developer=f"Failure To Record Login History: {str(e)}",
                code="SERVER_ERROR",
                status_code=1011,
                main_thread=False,
                param=user_instance.pk
            )

        # Send data to the frontend through websocket

        data = {}
        data["user"] = {
            "query_id": QueryID().get_query_id(user_instance.query_id)
        }

        user_device_instance = Device.objects.filter(
            user__query_id=user_instance.query_id).last()

        # If User Device Was Created Successfully,
        # Extract The Device's Token Data
        if user_device_instance:
            tokens = user_device_instance.tokens
            access = {
                "token": tokens.access_token,
                "exp": tokens.access_token_expires_at.isoformat()
            }
            refresh = {
                "token": tokens.refresh_token,
                "exp": tokens.refresh_token_expires_at.isoformat()
            }

        else:
            response.errors(
                field_error="Failure To Register Device",
                for_developer="Failure To Register Device",
                code="SERVER_ERROR",
                status_code=1011,
                main_thread=False,
                param=user_instance.pk
            )

        device_data = {}
        device_data["tokens"] = {}
        device_data["tokens"]["access"] = access
        device_data["tokens"]["refresh"] = refresh

        data["user"]["device"] = device_data

        """
        Data To Be Sent To WebSocket Should Be In The Json Format
        {
            "user": {
                "query_id": ***,
                "device": {
                    "tokens": {
                        "access": {
                            "token": ***,
                            "exp": ***
                        },
                        "refresh": {
                            "token": ***,
                            "exp": ***
                        }
                    }
                }
            }
        }

        This Is To Ensure Consistency Throughout The Application.
        Although The User Can Use More Than One Device At The Same Time, Only The
        Tokens For The Device Making The Request Should Be Sent
        """

        channel_layer = get_channel_layer()

        time.sleep(35)

        async def send_device_data():
            await channel_layer.group_send(
                f"user_{user_instance.pk}",
                {
                    'type': 'send.device_data',
                    'device_data': data,
                }
            )

        # Convert the asynchronous function to a synchronous one
        async_to_sync(send_device_data)()

        return

    def get_users(
        self, users: Union[str, List[str]]
    ) -> Union[dict, List[dict]]:

        if isinstance(users, str):
            user_instance = User.get_user(query_id=users)
            serialized_data = UserSerializer(user_instance)
        elif isinstance(users, list):
            user_instance = User.get_user(query_id=users)
            serialized_data = UserSerializer(
                user_instance, many=True
            )

        return (
            serialized_data.data
            if serialized_data
            else None
        )

    # Define a method that handles GET requests
    def get(self, request):

        is_single_user = request.GET.get("user", None)
        is_multiple_users = request.GET.get("users", None)

        if is_single_user or is_multiple_users:
            get_users = self.get_users(
                is_single_user
                if is_single_user
                else is_multiple_users
            )

        else:
            user_instance = User.objects.all()
            serialized_data = UserSerializer(
                user_instance, many=True
            )
            get_users = (
                serialized_data.data
                if serialized_data
                else None
            )

        return (
            Response(
                get_users,
                status=status.HTTP_200_OK
            )
            if get_users
            else Response(
                status=status.HTTP_400_BAD_REQUEST
            )
        )
