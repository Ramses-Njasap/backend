from django.db import models
from django.contrib.auth.models import Group as BaseGroup
from django.core.validators import (RegexValidator, MinLengthValidator)
from django.utils.translation import gettext_lazy as _

from accounts.models.auth import AuthCredential
from accounts.managers.profiles import UserProfileManager

from utilities import response

import base64


class Group(models.Model):
    """
    Customizing Default Authorizing Group To Hold Group Types
    """

    class GroupType(models.TextChoices):
        COURSES = "COURSES", _("Courses")
        ESTATES = "ESTATES", _("Estates")
    
    base_group = models.OneToOneField(
        BaseGroup, on_delete=models.CASCADE, primary_key=True,
    )
    _type = models.CharField(max_length=20, choices=GroupType.choices)

    class Meta:
        unique_together = ["_type", "base_group"]


class UserProfile(models.Model):

    class UserGender(models.TextChoices):
        MALE = "MALE", _("Male")
        FEMALE = "FEMALE", _("Female")
        OTHER = "OTHER", _("Other")
    
    class Status(models.TextChoices):
        STUDENT = "STUDENT", _("Student")
        REALTOR = "REALTOR", _("Realtor")
        LANDLORD = "LANDLORD", _("Landlord")
    
    # Making the default value for the field `statuses` to be a callable
    # instead of an instance ([]) so that it is not shared between all field instances
    def default_statuses():
        return []
    
    # User statuses like this:
    # user_profile = UserProfile.objects.create(user=user_instance)
    # user_profile.statuses.add(Status.REALTOR, Status.STUDENT)
    statuses = models.JSONField(default=default_statuses)
    user = models.OneToOneField(AuthCredential, on_delete=models.CASCADE)
    groups = models.ManyToManyField(Group, related_name="students", blank=True)
    phone = models.CharField(null=True, blank=True, max_length=16,
                             validators=[
                                 MinLengthValidator(8,
                                 message="Phone number must be entered in the format: '+999999999'. With a minimum of 8 digits allowed."),
                                 RegexValidator(regex=r"^\+[0-9]{7,15}$",
                                 message="Phone number must be entered in the format: '+999999999'. From 8 up to 16 digits allowed."),
                            ])
    legal_name = models.CharField(max_length=50, null=True, blank=True)
    gender = models.CharField(max_length=8, choices=UserGender.choices, default=UserGender.OTHER)
    date_of_birth = models.DateField(null=True, blank=True)

    objects = UserProfileManager()

    # @classmethod
    # def check_existence(cls, query_id: str) -> bool:

    #     manager = cls.verify

    #     query_id = base64.b64decode(query_id.encode())

    #     return manager.user_exists(query_id)
    
    @classmethod
    def get_profile(cls, query_id: str, is_active: bool = True) -> dict:

        manager = cls.objects

        if is_active:
            return manager.get_active_profile(query_id)
        
        return manager.get_inactive_profile(query_id)
    
    def set_statuses(self, *statuses):
        for status in statuses:
            if status not in [choice[0] for choice in UserProfile.Status.choices]:
                response.errors(
                    field_error="Invalid User Status",
                    for_developer=f"{status} Is Not A Valid Status",
                    code="BAD_REQUEST",
                    status_code=400
                )
        
        self.statuses = list(statuses)

        self.save()

    def get_statuses(self):
        return self.statuses

    def __str__(self):
        return self.user.username