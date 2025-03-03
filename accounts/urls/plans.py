from django.urls import path, re_path

from accounts.views.plans import (
    SubscriptionPlanView, PlanFeatureAPIView,
)

app_name = 'plans'
urlpatterns = [
    path(
        "",
        SubscriptionPlanView.as_view(),
        name="plan"),
    re_path(
        r"^features(?:/(?P<pk>\d+))?/$",
        PlanFeatureAPIView.as_view(),
        name="default"
    )
]
