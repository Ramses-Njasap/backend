from django.db import models


class Application(models.Model):
    name = models.CharField(max_length=100, unique=True, null=False, blank=False)
    users = models.ManyToManyField('User', through='ApplicationUser')


class ApplicationUser(models.Model):
    user = models.ForeignKey('User', on_delete=models.CASCADE, null=False)
    application = models.ForeignKey(
        'Application', on_delete=models.CASCADE, null=False)
    datetime_joined = models.DateTimeField()
    roles = models.ManyToManyField('Roles')

    class Meta:
        unique_together = ['user', 'application']


class Roles(models.Model):
    name = models.CharField()
    application = models.OneToOneField(
        'Application', on_delete=models.CASCADE, null=False)
