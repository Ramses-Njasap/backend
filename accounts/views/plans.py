from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework import serializers

from django.shortcuts import get_object_or_404
from django.db import models

from accounts.models.plans import (
    DefaultFeature,
    SubscriptionPlan, UserSubscriptionPlan
)
from accounts.models.users import User

from accounts.serializers.plans import (
    DefaultFeatureSerializer,
    SubscriptionPlanSerializer,
    UserSubscriptionPlanSerializer
)

from utilities import response
from utilities.views.accounts.plans import check_user_plan_decorator

from typing import Union, Optional

import base64
import importlib


class PlanFeatureAPIView(APIView):
    """
    API View to handle CRUD operations for DefaultFeature.
    """

    def get_user(self):
        user = User.objects.get(
            phone="+237693799106"
        )
        return user

    def get_serializer_class(
        self, plan_feature
    ) -> serializers.Serializer:

        plan_feature = f"{plan_feature}Serializer"

        try:
            # Dynamically import the serializers module
            # from accounts.serializers.plans
            module = importlib.import_module(
                "accounts.serializers.plans"
            )

            # Attempt to get the serializer class from the module
            serializer_class = getattr(module, plan_feature, None)

            if serializer_class is None:
                # Return None if the feature does
                # not match any serializer class
                response.errors(
                    field_error="Plan feature not found.",
                    for_developer=(
                        f"Serializer class with name: {plan_feature}"
                        " not found."
                    ),
                    code="INTERNAL_SERVER_ERROR",
                    status_code=500
                )

            # Return the found serializer class
            return serializer_class

        except ImportError as e:
            # Handle case where the module cannot be imported
            response.errors(
                field_error="Plan feature not found.",
                for_developer=(
                    f"Error importing serializers: {e}"
                ),
                code="INTERNAL_SERVER_ERROR",
                status_code=500
            )

    def get_serialized_data(
        self,
        # Single model instance or list of instances
        data: Union[models.Model, list[models.Model]],
        plan_feature: str, pk: bool,
        user: User
    ) -> Optional[Union[dict, list]]:

        """
        Serializes data based on the provided plan_feature
        and pk flag.

        Args:
            data (Union[models.Model, list[models.Model]]):
            The datato serialize, either a single model
            instance or a list of instances. plan_feature (str):
            The name of the plan feature, which determines the
            serializer to use. pk (bool): A flag indicating
            whether to use a single instance serializer or a
            many serializer. user (User): The user instance to
            include in the serializer context.

        Returns:
            Optional[Union[dict, list]]: Serialized data as a
            dictionary or list, or None if no serializer is found.
        """

        # Dynamically get the serializer class based on the plan_feature
        serializer_class = self.get_serializer_class(
            plan_feature=plan_feature
        )

        # Initialize the serializer with the data and context
        if pk:
            serializer_instance = serializer_class(
                data, context={
                    "user": user
                }
            )
        else:
            serializer_instance = serializer_class(
                data, many=True, context={
                    "user": user
                }
            )

        return serializer_instance.data
        # else:
        #     response.errors(
        #         field_error="Plan feature not found.",
        #         for_developer=(
        #             f"Serializer class {serializer_class} invalid"
        #         ),
        #         code="INTERNAL_SERVER_ERROR",
        #         status_code=500
        #     )

    def get_model(
        self, plan_feature: str
    ) -> models.Model:
        try:
            # Dynamically import the serializers module
            # from accounts.models.plans
            module = importlib.import_module(
                "accounts.models.plans"
            )

            # Attempt to get the model class from the module
            model_class = getattr(
                module, plan_feature, None
            )

            if model_class is None:
                # Return None if the feature does
                # not match any serializer class
                response.errors(
                    field_error="Plan feature not found.",
                    for_developer=(
                        f"Model class with name: {plan_feature} not found"
                    ),
                    code="BAD_REQUEST",
                    status_code=400
                )

            # Return the found serializer class
            return model_class

        except ImportError as e:
            # Handle case where the module cannot be imported
            response.errors(
                field_error="Plan feature not found.",
                for_developer=f"Error importing model: {e}",
                code="BAD_REQUEST",
                status_code=400
            )

    def get_model_instance_by_pk(
        self, pk: int, plan_feature: str
    ) -> models.Model:

        model = self.get_model(
            plan_feature=plan_feature
        )

        model_data = get_object_or_404(
            model, pk=pk
        )

        return model_data

    def get_all_model_instances(
        self, plan_feature: str
    ) -> models.QuerySet:

        model = self.get_model(
            plan_feature=plan_feature
        )

        model_data = model.objects.all()

        return model_data

    def get_plan(
        self, pk: int, user: User, plan_feature: str
    ) -> Response:

        if pk:
            feauture = self.get_model_instance_by_pk(
                pk=pk, plan_feature=plan_feature
            )
            serializer_data = self.get_serialized_data(
                data=feauture, plan_feature=plan_feature,
                pk=True, user=user
            )

        else:
            features = self.get_all_model_instances(
                plan_feature=plan_feature
            )
            serializer_data = self.get_serialized_data(
                data=features, plan_feature=plan_feature,
                pk=False, user=user
            )

        return Response(
            serializer_data, status=status.HTTP_200_OK
        )

    def get(self, request, pk=None, *args, **kwargs):
        """
        Handles GET requests.
        If `pk` is provided, retrieve a single feature;
        otherwise, list all features.
        """

        user = self.get_user()

        plan_feature = request.query_params.get(
            "plan-feature", None
        )

        if plan_feature is None:
            response.errors(
                field_error="None",
                for_developer="None"
            )

        return self.get_plan(
            plan_feature=plan_feature, pk=pk,
            user=user
        )

    def post(self, request, *args, **kwargs):
        """
        Handles POST requests to create a new DefaultFeature.
        """
        serializer = DefaultFeatureSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk=None, *args, **kwargs):
        """
        Handles PUT requests to update an existing DefaultFeature.
        """
        if not pk:
            return Response(
                {"error": "Method PUT requires a resource ID."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        feature = get_object_or_404(DefaultFeature, pk=pk)
        serializer = DefaultFeatureSerializer(feature, data=request.data, partial=False)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk=None, *args, **kwargs):
        """
        Handles PATCH requests to partially update an existing DefaultFeature.
        """
        if not pk:
            return Response(
                {"error": "Method PATCH requires a resource ID."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        feature = get_object_or_404(DefaultFeature, pk=pk)
        serializer = DefaultFeatureSerializer(feature, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk=None, *args, **kwargs):
        """
        Handles DELETE requests to delete an existing DefaultFeature.
        """
        if not pk:
            return Response(
                {"error": "Method DELETE requires a resource ID."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        feature = get_object_or_404(DefaultFeature, pk=pk)
        feature.delete()
        return Response(
            {"message": f"DefaultFeature with ID {pk} has been deleted."},
            status=status.HTTP_204_NO_CONTENT,
        )


class SubscriptionPlanView(APIView):

    @property
    def get_main_plans(self):
        main = ["standard", "business"]

        plan_instances = SubscriptionPlan.objects.filter(
            name__in=main
        ).order_by("pk")

        return plan_instances

    @property
    def get_custom_plans(self):

        plan_instances = SubscriptionPlan.objects.filter(
            is_custom=True
        )

        return plan_instances

    def get(self, request):

        plan_instances = SubscriptionPlan.objects.all()

        lists = request.query_params.get(
            "lists", None
        )

        if lists:
            if lists.lower() == "main":
                plan_instances = self.get_main_plans
            elif lists.lower() == "inbuilt":
                plan_instances = self.get_custom_plans

        serializer_data = SubscriptionPlanSerializer(
            plan_instances, many=True
        ).data

        return Response(serializer_data)


class UserSubscriptionPlanView(APIView):

    def get_permissions(self):
        # Applying IsAuthenticated only for the post method
        if not (self.request.method == 'POST', self.request.method == "GET"):
            return [IsAuthenticated()]
        return []

    def check_user_plan_before_post(self, user_id, plan_id):
        # Check if the user already has a plan with the given plan_id
        existing_plan = UserSubscriptionPlan.objects.filter(
            user=user_id, plan=plan_id).exists()
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
                except (ValueError, TypeError):
                    # setting error messages for user and developer respectively
                    field_message = ("Error Occurred In Plan Selection."
                                     " Contact Customer Support (Err - 001)")
                    for_developer = (f"""`plan` key value should be
                                     of type <class 'int'>
                                     representing a `SubscriptionPlan`
                                     instance and not {type(plan_id)}""")

                    # Raising error responses
                    response.errors(
                        field_error=field_message,
                        for_developer=for_developer,
                        code="INVALID_PARAMETER",
                        status_code=400)

            else:
                plan_instance = SubscriptionPlan.get_active_plan(pk=plan_id)

        else:
            # setting error messages for user and developer respectively
            field_message = ("Error Occurred In Plan Selection."
                             " Contact Customer Support (Err - 002)")
            for_developer = "`plan` key is required in request body"

            # Raising error responses
            response.errors(
                field_error=field_message,
                for_developer=for_developer,
                code="BAD_REQUEST", status_code=400)

        plan_instance = SubscriptionPlan.get_active_plan(pk=plan_id)

        return plan_instance.pk

    def get_user_pk(self, user_query_id) -> int:

        if user_query_id:
            try:
                user_instance = User.get_user(query_id=user_query_id)
            except base64.binascii.Error as e:
                # setting error messages for user nad developer respectively
                field_message = ("Server Error."
                                 " Contact Customer Support.")
                for_developer = (f"""`User Unique Identifier Error
                                 (base64.binascii Error): {e}""")

                # Raising error responses
                response.errors(
                    field_error=field_message,
                    for_developer=for_developer,
                    code="BAD_REQUEST", status_code=400)

            except Exception as e:
                # setting error messages for user nad developer respectively
                field_message = "Server Error. Contact Customer Support."
                for_developer = f"{e}"

                # Raising error responses
                response.errors(field_error=field_message,
                                for_developer=for_developer,
                                code="BAD_REQUEST", status_code=400)

        else:
            # setting error messages for user nad developer respectively
            field_message = "User Not Found. Contact Customer Support."
            for_developer = ("In Creation Of User Plan View,"
                             " `user_query_id` Wasn't Passed To"
                             " `get_user_instance` Function.")

            # Raising error responses
            response.errors(field_error=field_message,
                            for_developer=for_developer,
                            code="BAD_REQUEST", status_code=400)

        return user_instance.pk

    @check_user_plan_decorator
    def post(self, request):

        # payment_data = request.data.pop("payment", None)

        # request.data["user"] = self.get_user_instance(request.data["user"])
        request.data["user"] = self.get_user_pk(request.data["user"])
        # request.data["plan"] = self.get_plan_instance(request.data["plan"])

        # Create `UserSubscriptionPlan` serializer instance
        # using request data and parsing request
        # to serializer class for extra functionality on request
        serializer = UserSubscriptionPlanSerializer(
            data=request.data, context={"data": request.data})

        if serializer.is_valid():
            serializer.save()

            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors)

    def get(self, request):
        plan_instances = UserSubscriptionPlan.objects.all()
        serializer_data = UserSubscriptionPlanSerializer(plan_instances, many=True).data

        return Response(serializer_data)
