from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from utilities.generators.tokens import UserAuthToken
from utilities.permissions import DeviceAuthPermission


class RefreshAccessToken(APIView):
    permission_classes = (DeviceAuthPermission,)

    def post(self, request):

        renew = True if self.request.GET.get("renew") else False

        refresh_token = request.data["refresh_token"]

        # Initializing `UserAuthToken`

        user_auth_token =  UserAuthToken()

        access, refresh = user_auth_token.refresh_access_token(refresh_token=refresh_token, renew=renew)

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
        data["user"] = {
            "tokens": tokens_data
        }

        return Response(data, status=status.HTTP_200_OK)