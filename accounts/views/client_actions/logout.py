from django.utils import timezone

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from utilities import response
from utilities.permissions import GrantPermission

from accounts.models.devices import Device, DeviceLoginHistory


class Logout:
    """
    This Logs Out The User From A Remote Device. Since It Isn't Safe To Share User Token
    Attributed To A Single Device To Other Remote Devices, We Have To Set The Logout History
    For That Remote Device. If Any New Activity Is Detected By That Same Device, We Check If The Last
    Previous Activity For That Device Was A Logout, If it Was, We Redirect The User To Login Manually Rather
    Than Automatically Logging The User In. Otherwise, We Automatically Log The User In On That Device.
    """
    
    def __init__(self, request):
        self.request = request

    def set_logout_history(self, device_id: int):
        try:
            device_instance = Device.objects.get(pk=device_id)
        except Device.DoesNotExist:
            response.errors(
                field_error="Logout Failed: Device Does Not Exist.",
                for_developer="Logout Failed: Device Does Not Exist. It Might Have Been Deleted. Try To Reload Page.",
                code="NOT_FOUND",
                status_code=404
            )
        except Exception as e:
            response.errors(
                field_error="Logout Failed",
                for_developer=f"Logout Failed: {str(e)}.",
                code="INTERNAL_SERVER_ERROR",
                status_code=500
            )
        
        _is_logout_history_set = self._set_logout_history(device_instance=device_instance)

        if _is_logout_history_set:
            return True
        else:
            return False
    
    def _set_logout_history(self, device_instance):
        device_login_history_instances = DeviceLoginHistory.objects.filter(device=device_instance)

        # Getting Most Recent Login History
        latest_login_history_instance = device_login_history_instances.order_by("-login_at").first()

        if latest_login_history_instance:
            latest_login_history_instance.logout_at = timezone.now()
        else:
            response.errors(
                field_error="Logout Failed",
                for_developer="Logout Failed: No Login History For This Device Was Found.",
                code="NOT_FOUND",
                status_code=404
            )
        
        return not None

    def logout(self):

        device_id = self.request.data.pop("device_id", None)

        if device_id is None:
            response.errors(
                field_error="`device_id` field is required in REQUEST BODY",
                for_developer="`device_id` field is required in REQUEST BODY",
                code="BAD_REQUEST",
                status_code=404
            )

        _is_logout_successful = self.set_logout_history(device_id=device_id)

        if _is_logout_successful:
            return Response(status=status.HTTP_205_RESET_CONTENT)
        
        else:
            response.errors(
                field_error="An Error Occured. Try Again Or Contact Support",
                for_developer="An Error Occured. Try Again Or Contact Support",
                code="NOT_IMPLEMENTED",
                status_code=501
            )