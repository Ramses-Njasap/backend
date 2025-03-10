from typing import List, Union
from django.db import models
from django.db.models import Q
from django.contrib.auth.models import (AbstractBaseUser, PermissionsMixin)
from django.utils.timezone import now

from rest_framework.exceptions import ValidationError

# custom imports
from accounts.managers.users import (CreateUserManager,
                                     GetUserManager, VerifyUserManager)

from utilities import response
from utilities.generators.string_generators import (generate_name, QueryID, Keys)

# python imports
import uuid
import base64


class BannedPhoneNumber(models.Model):

    number = models.CharField(max_length=16, unique=True)
    datetime_banned = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.number} (Banned on {self.datetime_banned})"


class BannedEmail(models.Model):

    email = models.EmailField(unique=True)
    datetime_banned = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.email} (Banned on {self.datetime_banned})"


class APIKey(models.Model):
    user = models.ForeignKey(
        "User", on_delete=models.CASCADE,
        related_name="api_keys"
    )

    key = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    query_id = models.BinaryField(
        null=False, blank=False, max_length=10000,
        db_index=True
    )

    scopes = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "API Key"
        verbose_name_plural = "API Keys"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name or 'API Key'} for {self.user.username}"

    # @staticmethod
    # def generate_key():
    #     """Generate a secure random API key."""
    #     return secrets.token_urlsafe(40)

    # def save(self, *args, **kwargs):
    #     """Ensure the key is generated when creating a new instance."""
    #     if not self.key:
    #         self.key = self.generate_key()
    #     super().save(*args, **kwargs)

    def is_expired(self):
        """Check if the key is expired."""
        return self.expires_at and now() > self.expires_at

    def deactivate(self):
        """Deactivate the API key."""
        self.is_active = False
        self.save()

    def activate(self):
        """Activate the API key."""
        self.is_active = True
        self.save()

    def add_scope(self, scope):
        """Add a scope to the API key."""
        if not self.scopes:
            self.scopes = scope
        else:
            existing_scopes = self.scopes.split(',')
            if scope not in existing_scopes:
                existing_scopes.append(scope)
                self.scopes = ','.join(existing_scopes)
        self.save()

    def remove_scope(self, scope):
        """Remove a scope from the API key."""
        if self.scopes:
            scopes = self.scopes.split(',')
            if scope in scopes:
                scopes.remove(scope)
                self.scopes = ','.join(scopes)
        self.save()


class User(AbstractBaseUser, PermissionsMixin):

    class UserType(models.TextChoices):
        BUYER = "BUYER", "buyer"
        INVESTOR = "INVESTOR", "investor"
        AGENT = "AGENT", "agent"
        COMPANY = "COMPANY", 'company'
        EXTERNAL = 'EXTERNAL', 'external'

    user_type = models.CharField(
        max_length=15, choices=UserType.choices,
        default=UserType.BUYER, db_index=True)

    username = models.CharField(max_length=19, unique=True, db_index=True)
    email = models.EmailField(blank=True, unique=True, null=True)
    phone = models.CharField(blank=True, unique=True, null=True, max_length=16)

    # security measures
    banned_numbers = models.ManyToManyField('BannedPhoneNumber')
    banned_emails = models.ManyToManyField('BannedEmail')

    # boolean fields
    is_staff = models.BooleanField(default=False, null=True)
    is_admin = models.BooleanField(default=False, null=True)
    is_superuser = models.BooleanField(default=False, null=True)
    is_active = models.BooleanField(default=False)

    # Remove `is_verified` and add a model called Badge.
    # `verification_badge` in `Badge`
    # should be the replacement of `is_verified` here.
    is_verified = models.BooleanField(default=False)

    # multilevel marketing user checker
    is_mlm_user = models.BooleanField(default=False)

    # external user checker.
    # external users are users who have been granted permission to use
    # the API on their websites. These websites has to be registered and
    # verified by our system before permission is granted
    is_external_user = models.BooleanField(default=False)

    # Account visibility hides the account online
    # status from other accounts irrespective
    # of whether the account/user is online.
    is_account_visible = models.BooleanField(default=True)

    # --> Account lock hides the online status of the
    # account, prevent people from seeing the account
    # (in search or any client e.g postman, website, mobile app etc)
    # thereby not being able to interact
    # with the locked account.
    # --> Locked accounts cannot interact with other accounts,
    # cannot perform any POST method, cannot send
    # messages but can view any resource with the right permission,
    # complete monetary transactions etc.
    is_account_locked = models.BooleanField(default=False)

    # Toggles the online status of the account/user
    is_online = models.BooleanField(default=False)

    # Blocked accounts are not deleted accounts,
    # they are not just accessible by anyone
    # for the period of 6 months or if user carries out
    # the neccessary requirements to unblock accounts
    is_account_blocked = models.BooleanField(default=False)

    # Deleted accounts triggered by a user will be kept
    # in the state of True for 28 days
    # Should in case user wants to undo delete action
    # otherwise the account will be deleted permanently
    is_account_deleted = models.BooleanField(default=False)

    datetime_joined = models.DateTimeField(auto_now_add=True)
    datetime_updated = models.DateTimeField(auto_now=True)
    last_login = models.DateTimeField(blank=True, null=True)
    last_logout = models.DateTimeField(blank=True, null=True)

    query_id = models.BinaryField(
        null=False, blank=False, max_length=10000, db_index=True)

    # Used for generating unique One Time Passwords (OTP) for `users` .
    secret_key = models.BinaryField(null=False, blank=False, max_length=46)

    # Field to determine the visibility of query_id field in requests
    _pk_hidden = models.BooleanField(default=False)

    objects = CreateUserManager()
    get_by = GetUserManager()

    # returns a boolean for every check (get value)
    verify = VerifyUserManager()

    USERNAME_FIELD = 'phone'
    REQUIRED_FIELDS = []

    def __str__(self) -> str:

        return str(self.username)

    # @property
    # def get_username(self):
    #     return self.username.lstrip("@")

    @classmethod
    def create_superuser(cls, phone: str,
                         password: str = None, **extra_fields) -> dict:

        manager = cls.objects

        return manager.create_superuser(phone, password, **extra_fields)

    @classmethod
    def create_admin(cls, phone: str,
                     password: str = None, **extra_fields) -> dict:

        manager = cls.objects

        return manager.create_admin(phone, password, **extra_fields)

    @classmethod
    def create_staff(cls, phone: str,
                     password: str = None, **extra_fields) -> dict:

        manager = cls.objects

        return manager.create_staff(phone, password, **extra_fields)

    # Override the default manager
    @classmethod
    def create_user(cls, **kwargs) -> dict:

        manager = cls.objects

        return manager.create(**kwargs)

    @classmethod
    def check_existence(cls, query_id: str) -> bool:

        manager = cls.verify

        query_id = base64.b64decode(query_id.encode())

        return manager.user_exists(query_id)

    @classmethod
    def get_user(
        cls, query_id: Union[str, List[str]]
    ) -> Union[dict, List[dict]]:

        manager = cls.get_by

        try:
            if isinstance(query_id, str):
                query_ids = base64.b64decode(query_id.encode())
            elif isinstance(query_id, list):
                query_ids = [
                    base64.b64decode(q_id.encode())
                    for q_id in query_id
                ]
        except Exception as e:
            response.errors(
                field_error="Unknown User ID. Try Again Or Contact Support.",
                for_developer=f"QueryID Data Encoding Error: {e}.",
                code="INTERNAL_SERVER_ERROR",
                status_code=500
            )

        return manager.query_id(query_ids)

    @property
    def get_secret_key(self):
        key = Keys()
        return key.to_base64_string(self.secret_key)

    @staticmethod
    def search(query: str) -> dict:

        # query_id_instance = QueryID()
        # query_id = query_id_instance.query_id(query_id=query_id)

        return User.objects.filter(
            Q(username__icontains=query)
            | Q(phone__icontains=query)
        )

    @property
    def _is_online(self):

        if self.last_login and self.last_logout:

            return self.last_login >= self.last_logout

        elif self.last_login:

            return True

        elif self.last_logout:

            return False

        else:

            return False

    def save(self, *args, **kwargs):

        if self.username:

            username = self.username.lstrip("@")
            username = username.replace(" ", ".")

            self.username = f'@{username}'

            # Check if the username already exists
            if User.objects.filter(
                    username=self.username).exclude(pk=self.pk).exists():

                raise ValidationError({'error': 'Username already exists.'})

        else:

            self.username = f'@{generate_name()}'

            while User.objects.filter(username=self.username).exists():
                self.username = f'@{generate_name()}'

        #
        # Building user_id_generator parameters
        #

        data = [self.user_type, self.username, self.phone, str(uuid.uuid5)]
        data_length = sum(len(item) for item in data)

        #
        # Stopped building user_id_generator parameters
        #

        query_id_instance = QueryID(data=data, length=data_length)

        # Generating query_id and saving it to database
        self.query_id = query_id_instance.to_database()

        # Generating Secret Key
        # Creating A New User Data List By Filtering
        # `user_data` values that are not integers, strings, bytes or bool
        filtered_user_data = [
            value for value in data
            if isinstance(value, (int, str, bytes, bool))
        ]

        key_instance = Keys(filtered_user_data, _type="secret")
        self.secret_key = key_instance.generate()

        super(User, self).save(*args, **kwargs)
