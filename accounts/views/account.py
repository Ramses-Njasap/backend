from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status


from accounts.models.users import User
from accounts.models.account import PhoneNumberVerificationOTP, EmailVerificationOTP

from accounts.serializers.users import UserSerializer

from utilities.account import OTP as _OTP
from utilities.views.accounts.plans import create_user_free_subscription_plan
from utilities.generators.tokens import UserAuthToken
from utilities.permissions import DeviceAuthPermission, GrantPermission


class VerificationView(APIView):
    """
    This View Verifies The Code Sent To Either The User's
    Phone Number Or To The User's Email.
    """

    def get_permissions(self):
        # Applying Different Permission Classes Based On URL Query
        if not self.request.GET.get("active-user"):
            return [DeviceAuthPermission()]
        
        return [GrantPermission()]

    def check_verification_validity(self, check_on, request_data, user_instance) -> bool:

        if check_on == "phone":   
            _otp_instance = _OTP(otp=request_data["otp"], user=user_instance, model=PhoneNumberVerificationOTP, database_actions=True)
        
        elif check_on == "email":
            _otp_instance = _OTP(otp=request_data["otp"], user=user_instance, model=EmailVerificationOTP, database_actions=True)

        is_otp_valid = _otp_instance.is_valid()

        if is_otp_valid:
            return True
        
        return False
    
    def post(self, request):
        query_id = self.request.GET.get("query-id", None)

        verification_type = self.request.GET.get("verify", None)

        user_exists = User.check_existence(query_id=query_id)

        if user_exists:
            user_instance = User.get_user(query_id=query_id)

            if verification_type and (verification_type.lower() == "phone" or verification_type.lower() == "email"):

                is_valid = self.check_verification_validity(check_on=verification_type.lower(), request_data=request.data, user_instance=user_instance)

            # Instantiating UserAuthToken
            auth_tokens = UserAuthToken(user=user_instance)

            # Getting access token and refresh token along side their expiration times in seconds
            access, refresh = auth_tokens.get_token_pair()

            user_instance.is_active = True
            user_instance.save()
        
            if is_valid:
                data = {}
                data["user"] = user_instance.pk

                # Setting Subscription Plan Attribute Data
                data["plan"] = 1
                data["duration_length"] = 0
                
                create_user_free_subscription = create_user_free_subscription_plan(data)

                user_serializer = UserSerializer(user_instance)

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

                user_data = user_serializer.data
    
                user_data["tokens"] = tokens_data

                return Response(user_data)
        
        return Response(status=status.HTTP_400_BAD_REQUEST)