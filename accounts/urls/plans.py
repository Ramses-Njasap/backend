from django.urls import path

from accounts.views.plans import UserSubscriptionPlanView


app_name='plans'
urlpatterns = [
     path('', UserSubscriptionPlanView.as_view(), name='plans')
]
