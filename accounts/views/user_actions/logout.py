from django.utils import timezone

from rest_framework.response import Response
from rest_framework import status

from utilities import response
from utilities.generators.tokens import UserAuthToken

from accounts.models.devices import DeviceToken, Device, DeviceLoginHistory


class Logout:

    def __init__(self, request):
        self.request = request

    def get_device_access_token(self, request):
        if "Device-Authorization" in request.headers:
            header_values = request.headers["Device-Authorization"]

            try:
                header_values = header_values.split(" ")
                access_token = header_values[1]
            except Exception as e:
                response.errors(
                    field_error="Logout Failed",
                    for_developer=(f"""Logout Failed: Failed To
                                   Load Device Access Token: {str(e)}"""),
                    code="INTERNAL_SERVER_ERROR",
                    status_code=500
                )

            return access_token
        else:
            response.errors(
                field_error="Logout Failed",
                for_developer=(
                    "Logout Failed: Failed To Load"
                    " Device Authentication Header"
                ),
                code="INTERNAL_SERVER_ERROR",
                status_code=500
            )

    def get_active_device_instance(self, request):
        access_token = self.get_device_access_token(request=request)

        try:
            device_token_instance = DeviceToken.objects.get(
                access_token=access_token)
        except DeviceToken.DoesNotExist:
            response.errors(
                field_error="Logout Failed",
                for_developer=("Device Token Does Not Exist."
                               " It Might Have Been Deleted During"
                               " This Process By An External Request"),
                code="INTERNAL_SERVER_ERROR",
                status_code=500
            )
        except Exception as e:
            response.errors(
                field_error="Failed To Logout",
                for_developer=f"Failed To Logout: {str(e)}",
                code="INTERNAL_SERVER_ERROR",
                status_code=500
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
                status_code=500
            )
        except Exception as e:
            response.errors(
                field_error="Failed To Logout",
                for_developer=f"Failed To Logout: {str(e)}",
                code="INTERNAL_SERVER_ERROR",
                status_code=500
            )

        return device_instance

    def set_device_logout_history(self, request):
        device_instance = self.get_active_device_instance(request=request)

        device_login_history_instances = DeviceLoginHistory.objects.filter(
            device=device_instance)

        # Getting the most recent login history associated with the device
        last_login_history_instance = device_login_history_instances.order_by(
            "-login_at").first()

        if last_login_history_instance:
            # Updating the logout_at field for the most recent login history
            last_login_history_instance.logout_at = timezone.now()
            last_login_history_instance.save()

            return not None
        else:
            response.errors(
                field_error="Logout Failed",
                for_developer="No login history found for this device",
                code="INTERNAL_SERVER_ERROR",
                status_code=500
            )

    def logout(self):

        refresh_token = self.request.data.pop("refresh_token", None)

        if refresh_token is None:
            response.errors(
                field_error="`refresh_token` field is required in REQUEST BODY",
                for_developer="`refresh_token` field is required in REQUEST BODY",
                code="BAD_REQUEST",
                status_code=404
            )

        user_auth_token_instance = UserAuthToken()

        if user_auth_token_instance.revoke_tokens(refresh_token=refresh_token):
            self.set_device_logout_history(request=self.request)
            return Response(status=status.HTTP_205_RESET_CONTENT)

        else:
            response.errors(
                field_error="An Error Occured. Try Again Or Contact Support",
                for_developer="An Error Occured. Try Again Or Contact Support",
                code="NOT_IMPLEMENTED",
                status_code=501
            )
