from rest_framework.response import Response
from rest_framework import status

from accounts.serializers.plans import UserSubscriptionPlanSerializer
from functools import wraps


def check_user_plan_decorator(func):
    @wraps(func)
    def wrapper(self, request, *args, **kwargs):
        user_query_id = request.data.get("user")
        plan_id = request.data.get("plan")

        user_id, plan_id = self.get_user_and_plan(user_query_id, plan_id)

        # Check if the user already has a plan with the given plan_id
        if self.check_user_plan_before_post(user_id, plan_id):
            error_message = "User already has a plan with the specified plan_id."
            return Response({'error': error_message}, status=status.HTTP_400_BAD_REQUEST)

        return func(self, request, *args, **kwargs)

    return wrapper


def create_user_free_subscription_plan(data):

        # Create `UserSubscriptionPlan` serializer instance using request data and parsing request
        # to serializer class for extra functionality on request
        serializer = UserSubscriptionPlanSerializer(data=data, context={"data": data})

        if serializer.is_valid():
            serializer.save()

            return serializer.data
        
        return serializer.errors