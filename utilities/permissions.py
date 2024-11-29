from django.conf import settings
from django.db import models

from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework import serializers

from accounts.models.users import User
from accounts.models.devices import Device, DeviceToken, DeviceLoginHistory

from utilities.generators.tokens import DeviceAuthenticator
from utilities.account import CheckVerifiedCredentials
from utilities import response


# Returning Response That Aren't Errors
def perm_response(res, status_code: int = 200):

    raise_perm_response = serializers.ValidationError(res)
    raise_perm_response.status_code = status_code
    raise raise_perm_response


class UserAuthPermission(BasePermission):

    def check_user_active_status(self, request):
        if not request.user.is_active:
            response.errors(
                field_error=(
                    "User Inactive -"
                    " Can't Grant User Permission"
                ),
                for_developer=(
                    "User Inactivate -"
                    " Can't Grant User Permission"
                ),
                code="PRECONDITION_FAILED",
                status_code=412
            )

        return True

    def has_permission(self, request, view):

        # Check if Content-Type is not in request header
        # If it is not in request header, raise appropriate error

        if "Content-Type" not in request.headers:

            response.errors(
                field_error=(
                    "The 'Content-Type' header"
                    " is missing in the request."
                ),
                for_developer=(
                    "The 'Content-Type' header"
                    " is missing in the request."
                ),
                code="CONTENT_TYPE_MISSING",
                status_code=401
            )

        # Check if Content-Type is `application/json`
        # if it is not `application/json` raise appropriate error
        # Note: It is ideal to use json for API based systems

        if request.headers["Content-Type"] != "application/json":

            response.errors(
                field_error=(
                    "The 'Content-Type' header must be set"
                    " to 'application/json' for this request."
                ),
                for_developer=(
                    f"""You currently have
                     {request.META.get('CONTENT_TYPE')} as
                     Content-Type value instead of
                     'application/json'"""
                ),
                code="INVALID_CONTENT_TYPE",
                status_code=400
            )

        # Create Authentication class instance
        authentication = IsAuthenticated()

        # User authentication instance to grab
        has_permission = authentication.has_permission(
            request, view
        )

        if not has_permission:

            response.errors(
                field_error=(
                    "You do not have permission"
                    " to access this resource."
                ),
                for_developer=(
                    f"""You do not have permission to
                     perform a `{request.META.get('REQUEST_METHOD')}`
                     method on {request.META.get('PATH_INFO')}."""
                ),
                code="FORBIDDEN_ACCESS",
                status_code=403
            )

        # Checking User Active Status.
        # Throw An Error If User Is Not Active

        self.check_user_active_status(request=request)

        return True


class IsAdminUser(BasePermission):

    def has_permission(self, request, view):

        if "Content-Type" not in request.headers:
            return False

        # Check if the user is authenticated and an admin
        authentication = IsAuthenticated()
        if not authentication.has_permission(request, view):
            return False

        user = request.user
        if not user.is_authenticated or not user.is_staff:
            return False

        return True


class DeviceAuthPermission(BasePermission):
    def get_user_by_query_id(self, request):
        query_id = request.GET.get("query-id", None)

        user_instance = User.get_user(query_id=query_id)

        return user_instance

    def get_user_from_request_data(self, request_data):

        if "email_or_phone" not in request_data:
            response.errors(
                field_error=(
                    "Something Went Wrong In"
                    " Authenticating This Device"
                ),
                for_developer=(
                    "Device Authentication Failed:"
                    " No Device Token And `email_or_phone`"
                    " Attribute in `request body`"
                ),
                code="BAD_REQUEST",
                status_code=400
            )

        email_or_phone = request_data["email_or_phone"]

        # Check if the input is an email or a phone number
        user_instance = User.objects.filter(
            models.Q(email=email_or_phone) | models.Q(phone=email_or_phone)
        ).first()

        if not user_instance:
            response.errors(
                field_error=(
                    f"""Failed To Authenticate User:
                     User With Credential {email_or_phone}
                     Does Not Exist."""
                ),
                for_developer=(
                    f"""Device Authentication Failed:
                     No Device Token And No User With Credential
                     {email_or_phone} Exist."""
                ),
                code="BAD_REQUEST",
                status_code=400
            )

        return user_instance

    def validate_device_token(self, request, access_token):

        device_authenticator = DeviceAuthenticator()

        # Checking If Device Access Token Is Valid.
        # If No Errors Are Raised Then It Is Valid

        device_authenticator.verify_access_token(
            access_token
        )

        try:
            device_token_instance = DeviceToken.objects.get(
                access_token=access_token
            )
        except DeviceToken.DoesNotExist as e:
            response.errors(
                field_error="Server Error. Contact Support.",
                for_developer=f"{str(e)}",
                code="SERVER_ERROR",
                status_code=500
            )
        except Exception as e:
            response.errors(
                field_error="Server Error. Contact Support.",
                for_developer=f"{str(e)}",
                code="SERVER_ERROR",
                status_code=500
            )

        try:
            device_instance = Device.objects.get(
                tokens=device_token_instance
            )
        except Device.DoesNotExist as e:
            response.errors(
                field_error="Server Error. Contact Support.",
                for_developer=f"{str(e)}",
                code="SERVER_ERROR",
                status_code=500
            )
        except Exception as e:
            response.errors(
                field_error="Server Error. Contact Support.",
                for_developer=f"{str(e)}",
                code="SERVER_ERROR",
                status_code=500
            )

        # Update This To Check For Anonymous User Instead
        if request.user is None:
            response.errors(
                field_error="User Not Authenticated.",
                for_developer=(
                    "User Cannot Be Anonymous."
                    " User Authentication (Login) Is Required"
                ),
                code="BAD_REQUEST",
                status_code=400
            )

        user_instance = self.get_user_by_query_id(request=request)

        if device_instance.user != user_instance:
            response.errors(
                field_error="Device Doesn't Recognise This User.",
                for_developer=(
                    "Every Device Is Assigned To A User."
                    " Device Doesn't Recognise This User"
                ),
                code="SERVER_ERROR",
                status_code=400
            )

        # No Need To Check Login History During Login
        base_login_url = settings.APPLICATION_SETTINGS["LOGIN_URL"]["BASE"]
        relative_login_url = settings.APPLICATION_SETTINGS["LOGIN_URL"]["URL"]
        login_url = base_login_url + relative_login_url
        if request.path.lstrip("/") != login_url:
            _login_history = self.check_login_history(
                device_instance=device_instance
            )

            if _login_history:
                return True
            else:
                return False

    def check_device_authentication_header(self, request):
        if "Device-Authorization" in request.headers:
            header_values = request.headers["Device-Authorization"]

            try:
                header_values = header_values.split(" ")
                token_type = header_values[0]
                access_token = header_values[1]
            except Exception as e:
                response.errors(
                    field_error="Error In Getting Device Token",
                    for_developer=f"{str(e)}",
                    code="BAD_REQUEST",
                    status_code=400
                )

            if token_type not in settings.DEVICE_JWT["AUTH_HEADER_TYPE"]:
                response.errors(
                    field_error=(
                        "Something Went Wrong In"
                        " Authenticating This Device"
                    ),
                    for_developer=(
                        f"""Device Authentication Failed:
                         {token_type} Not Found In
                         {settings.DEVICE_JWT['AUTH_HEADER_TYPE']}"""
                    ),
                    code="BAD_REQUEST",
                    status_code=400
                )

            is_device_token_validated = self.validate_device_token(
                request=request, access_token=access_token
            )

            if is_device_token_validated:
                return True

        else:
            # No Need To Check Login History During Login
            # Extract login URL components
            base_login_url = settings.APPLICATION_SETTINGS["LOGIN_URL"]["BASE"]
            relative_login_url = settings.APPLICATION_SETTINGS["LOGIN_URL"]["URL"]
            login_url = base_login_url + relative_login_url

            # Extract request login OTP URL components
            base_otp_url = settings.APPLICATION_SETTINGS["REQUEST_LOGIN_OTP"]["BASE"]
            relative_otp_url = settings.APPLICATION_SETTINGS["REQUEST_LOGIN_OTP"]["URL"]
            request_login_otp_url = base_otp_url + relative_otp_url

            login_path = request.path.lstrip("/")
            if login_path in {login_url, request_login_otp_url}:
                if not request.data:
                    response.errors(
                        field_error=(
                            "Something Went Wrong In"
                            " Authenticating This Device."
                        ),
                        for_developer=(
                            "Device Authentication Failed:"
                            " No Device Token And `request body` Not Found"
                        ),
                        code="BAD_REQUEST",
                        status_code=400
                    )

                user_instance = self.get_user_from_request_data(
                    request_data=request.data
                )

                # Performing Actions To Verify User With New
                # Device Attempting Login
                check_verified_credentials_instance = CheckVerifiedCredentials(
                    user_instance=user_instance
                )

                if check_verified_credentials_instance is None:
                    response.errors(
                        field_error=(
                            "Something Went Wrong In"
                            " Authenticating This Device."
                        ),
                        for_developer=(
                            "Device Authentication Failed:"
                            " No Device Token And Not A Trusted"
                            " Device To Perform Login With OTP."
                        ),
                        code="BAD_REQUEST",
                        status_code=400
                    )
                else:
                    credentials_instance = check_verified_credentials_instance
                    credentials = credentials_instance.is_phone_email_verified(
                        check_device=True
                    )
                    phone, email, device = credentials

                    send_otp_to = []

                    if phone[1]:
                        send_otp_to.append("phone")
                    if email[1]:
                        send_otp_to.append("email")
                    if device[1]:
                        send_otp_to.append(device[0])

                    perm_response(
                        res={"send_otp_to": send_otp_to}, status_code=307
                    )

            else:
                return False

    def check_login_history(self, device_instance):
        device_login_history_instances = DeviceLoginHistory.objects.filter(
            device=device_instance
        )

        latest_login_history_instance = device_login_history_instances.order_by(
            "-login_at"
        ).first()

        if latest_login_history_instance:
            if (
                (latest_login_history_instance.logout_at is not None)
                and (
                    latest_login_history_instance.logout_at
                    >= latest_login_history_instance.login_at
                )
            ):
                # Add Code To Revoke Device Token Cancelled.
                response.errors(
                    field_error=(
                        "User Has Been Logged Out."
                        " Try To Login Again"
                    ),
                    for_developer=(
                        "User Has Been Logged Out."
                        " Redirect To Login Page"
                    ),
                    code="TEMPORARY_REDIRECT",
                    status_code=307
                )

        else:
            return None

        return not None

    def has_permission(self, request, view):

        if "Content-Type" not in request.headers:
            response.errors(
                field_error=(
                    "The 'Content-Type' header is"
                    " missing in the Request Header."
                ),
                for_developer=(
                    "The 'Content-Type' header"
                    " is missing in the Request Header."
                ),
                code="BAD_REQUEST",
                status_code=400
            )

        else:
            if request.headers["Content-Type"] != "application/json":
                response.errors(
                    field_error=(
                        "The 'Content-Type' header must be set"
                        " to 'application/json' for this request."
                    ),
                    for_developer=(
                        "The 'Content-Type' header must be set"
                        " to 'application/json' for this request."
                    ),
                    code="BAD_REQUEST",
                    status_code=400
                )

        check_auth_header = self.check_device_authentication_header(
            request=request
        )
        if check_auth_header:
            return True

        response.errors(
            field_error=(
                "This device does not have permission"
                " to access this resource."
            ),
            for_developer=(
                f"""This device does not have permission to
                 perform a `{request.META.get('REQUEST_METHOD')}`
                 method on {request.META.get('PATH_INFO')}."""
            ),
            code="FORBIDDEN_ACCESS",
            status_code=403
        )


class GrantPermission(DeviceAuthPermission, UserAuthPermission):

    def has_permission(self, request, view):
        """
        Check For Device Permission First. The Backend
        Has Trusts With The Client (Device)
        More Than It Has Trust With The User.
        This Is Because The Client Is The One Interacting
        With The Server And Not The User. Instead, The User
        Creates Trust With The Client And Not
        With The Server. So, Validation Of The Client (Device)
        Is More Important Than The User.
        """
        # Checking (Client) Device Permission
        device_permission = super(
            DeviceAuthPermission, self
        ).has_permission(request, view)

        if not device_permission:
            return False

        # Checking (End) User Permission
        user_permission = super(
            UserAuthPermission, self
        ).has_permission(request, view)

        if not user_permission:
            return False

        # Return True only if both user and
        # device have permission
        return True
