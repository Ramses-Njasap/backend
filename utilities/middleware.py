# middleware.py
from django.http import (HttpRequest, JsonResponse)
from django.urls import is_valid_path, get_urlconf

from django_user_agents.utils import get_user_agent

from accounts.models.devices import Device


class IsUserRobot:
    def __init__(self, get_response):
        self.get_response = get_response

    def raise_error(
            self, code: str, status_code: int,
            field_error: str, for_developer: str
    ):

        error = {
            "message": {
                "request": code.replace("_", " "),
                "field": field_error,
            },
            "status": {
                "code": code,
                "status_code": status_code
            },
            "developer": for_developer
        }
        return JsonResponse(error, status=status_code)

    def __call__(self, request: HttpRequest):
        try:
            user_agent = get_user_agent(request)
        except Exception as e:
            return self.raise_error(
                code="INTERNAL_SERVER_ERROR",
                status_code=500,
                field_error="Unable To Read Device Properties",
                for_developer=str(e)
            )

        if not request.META.get('HTTP_USER_AGENT') or user_agent.is_bot:
            return self.raise_error(
                code="LOCKED",
                status_code=423,
                field_error="Bot Detected",
                for_developer="Bot Detected"
            )
        else:
            return self.get_response(request)


class DeviceMetaInfoMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def raise_error(
            self, code: str, status_code: int,
            field_error: str, for_developer: str
    ):

        error = {
            "message": {
                "request": code.replace("_", " "),
                "field": field_error,
            },
            "status": {
                "code": code,
                "status_code": status_code
            },
            "developer": for_developer
        }

        return JsonResponse(error, status=404)

    def __call__(self, request: HttpRequest):

        try:
            user_agent = get_user_agent(request)
        except Exception as e:
            self.raise_error(
                code="INTERNAL_SERVER_ERROR",
                status_code=500,
                field_error="Unable To Read Device Properties",
                for_developer=str(e)
            )

        # Getting Device/Client Type
        if user_agent.is_mobile:
            device_type = Device.DeviceType.MOBILE
        elif user_agent.is_tablet:
            device_type = Device.DeviceType.TABLET
        elif user_agent.is_pc:
            device_type = Device.DeviceType.PC
        else:
            device_type = Device.DeviceType.OTHER

        # Getting Client Type
        if user_agent.browser:
            client_type_info = (
                f"""{user_agent.browser.family},
                {user_agent.browser.version_string}"""
            )
        else:
            client_type_info = "LaLodge APP, 0.1"

        meta_info = {
            # User Ip Address
            "ip": request.META.get("REMOTE_ADDR"),

            # Device type: Mobile, Tablet, PC, etc
            "device_type": device_type,

            # Device OS and OS Version
            "os_osversion": (
                f"""{user_agent.os.family},
                {user_agent.os.version_string}"""
            ),

            # Client Type and Client Version
            "client_clientversion": client_type_info,

            # User Agent
            "user_agent": user_agent,

            "host": request.META.get("REMOTE_HOST", None),
            "user-agent": request.META.get("HTTP_USER_AGENT", None),
            "connection": request.META.get("HTTP_CONNECTION", None),
            "content-length": request.META.get("CONTENT_LENGTH", None)
        }

        request.device_meta_info = meta_info
        return self.get_response(request)


class CheckUnmatchedURLMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: HttpRequest):
        response = self.get_response(request)

        # Check if the requested URL matches any
        # defined URL patterns
        if not is_valid_path(
            path=request.path_info.lstrip("/"),
            urlconf=get_urlconf()
        ):
            # If no URL pattern matches, return a JSON
            # response with an error message

            data = {'error': 'No matching URL pattern found.'}
            data['endpoint_status'] = 404

            # Include the original response data in the JSON response
            if response.status_code != 404:
                return response

            error = {
                "message": {
                    "request": "NOT FOUND",
                    "field": "No matching URL pattern found.",
                },
                "status": {
                    "code": "NOT_FOUND",
                    "status_code": 404
                },
                "developer": (
                    f"""{request.path_info.lstrip('/')}
                     Does Not Match Any URLs"""
                )
            }

            return JsonResponse(error, status=404)

        return response
