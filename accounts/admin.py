from django.contrib import admin
from accounts.models.users import User, APIKey
from accounts.models.mlm_user import MLMUser
from accounts.models.profiles import UserProfile
from accounts.models.plans import (
    DefaultFeature, AIConflictResolutionAssistantFeature,
    TeamGoalFeature, AIMarketingAssistantFeature,
    MultiLevelMarketingFeature, BusinessFeature,
    SubscriptionPlan, UserSubscriptionPlan
)

from accounts.models.account import (OTP, PhoneNumberVerificationOTP,
                                     EmailVerificationOTP, LoginOTP,
                                     UsedOTP, RealEstateCertification,
                                     KYCVerificationCheck, AccountVerification)

from accounts.models.devices import (DeviceLoginHistory, DeviceTokenBlacklist,
                                     DeviceToken, DeviceWallet, Device)


# Register your models here.
admin.site.register(User)
admin.site.register(APIKey)
admin.site.register(MLMUser)
admin.site.register(UserProfile)
admin.site.register(DefaultFeature)
admin.site.register(AIConflictResolutionAssistantFeature)
admin.site.register(TeamGoalFeature)
admin.site.register(AIMarketingAssistantFeature)
admin.site.register(MultiLevelMarketingFeature)
admin.site.register(BusinessFeature)
admin.site.register(SubscriptionPlan)
admin.site.register(UserSubscriptionPlan)

admin.site.register(OTP)
admin.site.register(PhoneNumberVerificationOTP)
admin.site.register(EmailVerificationOTP)
admin.site.register(LoginOTP)
admin.site.register(UsedOTP)
admin.site.register(RealEstateCertification)
admin.site.register(KYCVerificationCheck)
admin.site.register(AccountVerification)

admin.site.register(DeviceLoginHistory)
admin.site.register(DeviceTokenBlacklist)
admin.site.register(DeviceToken)
admin.site.register(DeviceWallet)
admin.site.register(Device)
