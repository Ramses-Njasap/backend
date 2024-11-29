from django.db import models

from utilities import response


class DeviceManager(models.Manager):
    def filter_by_user(self, user_instance) -> models.QuerySet:

        if not user_instance:
            field_message = "User Not Found"
            for_developer = ("User Instance Needs To Be Provided Before"
                             " Filtering Devices By User")

            # Raising error responses
            response.errors(field_error=field_message,
                            for_developer=for_developer,
                            code="BAD_REQUEST", status_code=400)

        instances = super().filter(user=user_instance)

        if not instances.exists():
            # setting error messages for user and developer respectively
            field_message = "Not Found"
            for_developer = "Query Returned None"

            # Raising error responses
            response.errors(field_error=field_message,
                            for_developer=for_developer,
                            code="NOT_FOUND", status_code=404)

        return instances
