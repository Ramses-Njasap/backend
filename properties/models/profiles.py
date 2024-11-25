from django.utils.translation import gettext_lazy as _
from django.contrib.gis.db import models
from accounts.models.profiles import UserProfile
from utilities import response


class Profile(models.Model):

    class UserType(models.TextChoices):
        COMPANY = 'COMPANY', _('Company')
        INDIVIDUAL = 'INDIVIDUAL', _('Individual')
    
    class Status(models.TextChoices):
        REALTOR = 'REALTOR', _('Realtor')
        LANDLORD = 'LANDLORD', _('Landlord')
        AGENT = 'AGENT', _('Agent')
        BUYER = 'BUYER', _('Buyer')

    def default_statuses():
        return []

    statuses = models.JSONField(default=default_statuses)
    user = models.OneToOneField(UserProfile, on_delete=models.CASCADE)
    boundary = models.PolygonField(geography=True, srid=4326)
    central_coordinate = models.JSONField()
    location_name = models.CharField(max_length=255, null=True, blank=True)
    user_type = models.CharField(max_length=15, choices=UserType.choices, default=UserType.INDIVIDUAL, db_index=True)
    name = models.CharField(max_length=70, null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'LaLouge Estate User Profile'
        verbose_name_plural = 'LaLouge Estate User Profiles'
    
    def __str__(self):
        return f"{self.user.user.name}" if self.user and self.user.user else "Unknown User"
    
    def set_statuses(self, *statuses):
        valid_statuses = [choice[0] for choice in Profile.Status.choices]
        
        for status in statuses:
            if status not in valid_statuses:
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
    
    def save(self, *args, **kwargs):
        # Ensure statuses defaults to `BUYER` if profile has no status
        if not self.statuses:
            self.statuses = [Profile.Status.BUYER]

        # Check if profile is newly created by inspecting if the db table column has an id
        is_new = self.pk is None

        # Deactivate the profile if the class instance is newly created
        # and user is not a Buyer
        if is_new and Profile.Status.BUYER not in self.statuses:
            self.is_active = False
        
        super().save(*args, **kwargs)
