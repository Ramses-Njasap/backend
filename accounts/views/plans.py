from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from accounts.models.plans import SubscriptionPlan, UserSubscriptionPlan
from accounts.models.auth import AuthCredential

from accounts.serializers.plans import UserSubscriptionPlanSerializer

from utilities import response
from utilities.views.accounts.plans import check_user_plan_decorator

import base64


class UserSubscriptionPlanView(APIView):

    def get_permissions(self):
        # Applying IsAuthenticated only for the post method
        if not (self.request.method == 'POST', self.request.method == "GET"):
            return [IsAuthenticated()]
        return []

    def check_user_plan_before_post(self, user_id, plan_id):
        # Check if the user already has a plan with the given plan_id
        existing_plan = UserSubscriptionPlan.objects.filter(user=user_id, plan=plan_id).exists()
        return existing_plan

    def get_user_and_plan(self, user_query_id, plan_id):
        user_id = self.get_user_pk(user_query_id)
        plan_id = self.get_plan_instance(plan_id)
        return user_id, plan_id
    
    def get_plan_instance(self, plan_id) -> int:

        if plan_id:
            if not isinstance(plan_id, int):
                try:
                    plan_id = int(plan_id)
                except:
                    # setting error messages for user and developer respectively
                    field_message = f"Error Occurred In Plan Selection. Contact Customer Support (Err - 001)"
                    for_developer = f"`plan` key value should be of type <class 'int'> representing a `SubscriptionPlan` instance and not {type(plan_id)}"
                    
                    # Raising error responses
                    response.errors(field_error=field_message, for_developer=for_developer, code="INVALID_PARAMETER", status_code=400)
                
            else:
                plan_instance = SubscriptionPlan.get_active_plan(pk=plan_id)

        else:
            # setting error messages for user and developer respectively
            field_message = "Error Occurred In Plan Selection. Contact Customer Support (Err - 002)"
            for_developer = "`plan` key is required in request body"
            
            # Raising error responses
            response.errors(field_error=field_message, for_developer=for_developer, code="BAD_REQUEST", status_code=400)

        plan_instance = SubscriptionPlan.get_active_plan(pk=plan_id)

        return plan_instance.pk
    
    def get_user_pk(self, user_query_id) -> int:
        
        if user_query_id:
            try:
                user_instance = AuthCredential.get_user(query_id=user_query_id)
            except base64.binascii.Error as e:
                # setting error messages for user nad developer respectively
                field_message = "Server Error. Contact Customer Support."
                for_developer = f"`User Unique Identifier Error (base64.binascii Error): {e}"

                # Raising error responses
                response.errors(field_error=field_message, for_developer=for_developer, code="BAD_REQUEST", status_code=400)
            
            except Exception as e:
                # setting error messages for user nad developer respectively
                field_message = "Server Error. Contact Customer Support."
                for_developer = f"{e}"

                # Raising error responses
                response.errors(field_error=field_message, for_developer=for_developer, code="BAD_REQUEST", status_code=400)
        
        else:
            # setting error messages for user nad developer respectively
            field_message = "User Not Found. Contact Customer Support."
            for_developer = "In Creation Of User Plan View, `user_query_id` Wasn't Passed To `get_user_instance` Function."

            # Raising error responses
            response.errors(field_error=field_message, for_developer=for_developer, code="BAD_REQUEST", status_code=400)

        return user_instance.pk
    
    @check_user_plan_decorator
    def post(self, request):

        # payment_data = request.data.pop("payment", None)

        # request.data["user"] = self.get_user_instance(request.data["user"])
        request.data["user"] = self.get_user_pk(request.data["user"])
        # request.data["plan"] = self.get_plan_instance(request.data["plan"])

        # Create `UserSubscriptionPlan` serializer instance using request data and parsing request
        # to serializer class for extra functionality on request
        serializer = UserSubscriptionPlanSerializer(data=request.data, context={"data": request.data})

        if serializer.is_valid():
            serializer.save()

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors)
    
    def get(self, request):
        plan_instances = UserSubscriptionPlan.objects.all()
        serializer_data = UserSubscriptionPlanSerializer(plan_instances, many=True).data

        return Response(serializer_data)