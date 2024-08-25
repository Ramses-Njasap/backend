from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from accounts.models.users import User

from accounts.models.profiles import UserProfile
from accounts.serializers.profiles import UserProfileSerializer

from utilities.permissions import GrantPermission
from utilities import response
from rest_framework.parsers import JSONParser

import requests

"""
User Profiles are created automatically when user creates an account
so, no POST method in any of these classes.
"""

class UserProfileView(APIView):
    # permission_classes = (AuthPermission,)
    parser_classes = [JSONParser]

    """
    List all user profiles or create a new user profile.
    """

    def get_user_profiles(self, query_id=None):
        if query_id:

            try:
                user_instance = User.get_user(query_id)
            except User.DoesNotExist:
                response.errors(
                    field_error="User Not Found",
                    for_developer=f"No User With QueryID {query_id} Exists",
                    code="NOT_FOUND",
                    status_code=404,
                )
            
            except Exception as e:
                response.errors(
                    field_error="Failed To Get Users Data",
                    for_developer=f"{e}",
                    code="SERVER_ERROR",
                    status_code=500
                )
            
            if user_instance:
                try:
                    user_profile_instance = UserProfile.objects.get(user=user_instance)
                except UserProfile.DoesNotExist:
                    response.errors(
                        field_error="User Not Found",
                        for_developer=f"{str(e)}",
                        code="NOT_FOUND",
                        status_code=404
                    )
                
                except Exception as e:
                    response.errors(
                        field_error="Failed To Get Users Data",
                        for_developer=f"{str(e)}",
                        code="SERVER_ERROR",
                        status_code=500
                    )
                
                return user_profile_instance
        
        else:

            return UserProfile.objects.all()

    def get(self, request):
        ip_address = request.META.get('REMOTE_ADDR')
        url = f'https://ipinfo.io/154.72.153.201/json'
        response = requests.get(url)
        data = response.json()

        # ip_address = '8.8.8.8'  # Replace with the IP address you want to look up
        ip_info = data

        print(f"IP Address: {ip_info.get('ip')}")
        print(f"Location: {ip_info.get('city')}, {ip_info.get('region')}, {ip_info.get('country')}")
        print(f"Latitude/Longitude: {ip_info.get('loc')}")
        print(f"Device Type: Not available (IP addresses do not inherently provide device type information)")
        # Access query parameters
        query_params = request.query_params

        # Retrieve specific query parameters
        query_id = query_params.get("query-id", None)

        # user_profiles = self.get_user_profiles(query_id)
        
        return Response(UserProfileSerializer(self.get_user_profiles(query_id=query_id)).data) if query_id else Response(UserProfileSerializer(self.get_user_profiles(), many=True).data)