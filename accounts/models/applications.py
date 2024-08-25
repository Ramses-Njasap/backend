from django.db import models
from accounts.models.auth import AuthCredential


class Application(models.Model):
    name = models.CharField(max_length=100, unique=True, null=False, blank=False)
    users = models.ManyToManyField(AuthCredential, through='ApplicationUser')


class ApplicationUser(models.Model):
    user = models.ForeignKey(AuthCredential, on_delete=models.CASCADE, null=False)
    application = models.ForeignKey('Application', on_delete=models.CASCADE, null=False)
    datetime_joined = models.DateTimeField()
    roles = models.ManyToManyField('Roles')

    class Meta:
        unique_together = ['user', 'application']


class Roles(models.Model):
    name = models.CharField()
    application = models.OneToOneField('Application', on_delete=models.CASCADE, null=False)