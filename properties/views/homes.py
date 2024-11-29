from rest_framework.views import APIView

from accounts.models.users import User
from accounts.models.profiles import UserProfile

from properties.models.profiles import UserProfile as Profile
from properties.serializers.homes import HomeSerializer

from utilities import response

import threading


class HomeView(APIView):
    def get_user_profile_instance(self, query_id=None):
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
                    user_profile_instance = UserProfile.objects.get(
                        user=user_instance
                    )

                    profile_instance = Profile.objects.get(
                        user=user_profile_instance
                    )

                except UserProfile.DoesNotExist:
                    response.errors(
                        field_error="User Not Found",
                        for_developer="User Not Found",
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

                return profile_instance

        else:

            return Profile.objects.all()

    def post(self, request):

        # boundary = request.data.pop("boundary", [])
        # land_boundary = request.data.pop("land_boundary", {})
        # general_amenities = request.data.pop("general_amenities", {})
        # rooms = request.data.get("rooms", [])

        # Access query parameters
        query_params = request.query_params

        # Retrieve specific query parameters
        query_id = query_params.get("query-id", None)

        uploader = request.data.get("uploader", None)

        if not uploader:
            response.errors(
                field_error="Unidentified user",
                for_developer="`uploader` key missing in request data",
                code="BAD_REQUEST",
                status_code=400
            )
        else:
            uploader = self.get_user_profile_instance(query_id=query_id)
            request.data["uploader"] = uploader

        # Create home serializer instance using
        # request data and parsing request
        # to serializer class for extra functionality on request.
        serializer = HomeSerializer(
            data=request.data, context={'request': request}
        )

        if serializer.is_valid():
            home_instance = serializer.save()

            # Perform geolocation lookup in a separate thread
            geolocation_thread = threading.Thread(
                target=self.get_geolocation, args=(home_instance)
            )
            geolocation_thread.start()

    def thread2(self, home_instance):
        ...
