from django.contrib.auth.models import (UserManager)
from django.core.exceptions import ObjectDoesNotExist

from utilities import response

# CreateUserManager as Users model managers name is being used because
# it's parent class already has the name "UserManager".
# if changes have to be made on the naming, please, ensure it doesn't conflict
# with the parent class'

# Any changes on this class should be dealt with much caution


class CreateUserManager(UserManager):

    def _create_user(self, phone, password=None, **extra_fields):
        """
        Create and save a user with the given phone and password.
        """
        if not password:
            raise ValueError('You must provide a password')

        if not phone:
            raise ValueError('You must provide a phone number')

        # Check for unique constraint on phone
        if self.model.objects.filter(phone=phone).exists():
            raise ValueError('A user with this phone already exists.')

        # Create a new user object
        user = self.model(phone=phone, **extra_fields)

        # Set the user's password
        user.set_password(password)

        # Validate the user model and save it to the database
        # user.full_clean()
        user.save(using=self._db)

        return user

    def create_user(self, phone, password=None, **extra_fields):
        """
        Create a normal user.
        """
        # Ensure extra_fields is a dictionary
        extra_fields = extra_fields or {}

        # Set default values for is_staff and is_superuser
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_admin', False)
        extra_fields.setdefault('is_superuser', False)
        extra_fields['is_active'] = True

        # Call _create_user with the provided arguments
        return self._create_user(phone=phone, password=password, **extra_fields)

    def create_staff(self, phone, password=None, **extra_fields):
        """
        Create a staff member or an admin.
        """
        # Ensure extra_fields is a dictionary
        extra_fields = extra_fields or {}

        # Set default values for is_staff and is_superuser
        extra_fields['is_superuser'] = False
        extra_fields['is_admin'] = False
        extra_fields.setdefault('is_staff', True)
        extra_fields['is_active'] = True

        # Call _create_user with the provided arguments
        return self._create_user(phone=phone,
                                 password=password, **extra_fields)

    def create_admin(self, phone, password=None, **extra_fields):
        """
        Create a staff member or an admin.
        """
        # Ensure extra_fields is a dictionary
        extra_fields = extra_fields or {}

        # Set default values for is_staff and is_superuser
        extra_fields['is_superuser'] = False
        extra_fields['is_staff'] = True
        extra_fields.setdefault('is_admin', True)
        extra_fields['is_active'] = True

        # Call _create_user with the provided arguments
        return self._create_user(phone=phone,
                                 password=password, **extra_fields)

    def create_superuser(self, phone, password=None, **extra_fields):
        """
        Create a superuser.
        """
        # Ensure extra_fields is a dictionary
        extra_fields = extra_fields or {}

        # Set default values for is_staff and is_superuser
        extra_fields['is_admin'] = True
        extra_fields['is_staff'] = True
        extra_fields.setdefault('is_superuser', True)
        extra_fields['is_active'] = True

        # Call _create_user with the provided arguments
        return self._create_user(phone=phone, password=password, **extra_fields)

    def create_externaluser(self, phone, password=None, **extra_fields):
        """
        Create external users. External users are users who
        use the APIs on their own platform
        which is separate from our official platform
        """

        # Ensure extra_fields is a dictionary
        extra_fields = extra_fields or {}

        # Set default values for is_staff, is_admin, is_superuser to false
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_admin', False)
        extra_fields.setdefault('is_superuser', False)
        extra_fields.setdefault('is_active', False)

        # Call _create_user with the provided arguments
        return self._create_user(phone=phone, password=password, **extra_fields)


class GetUserManager(UserManager):

    def phone(self, phone):
        """
        Retrieve user with phone
        """
        return self.get(phone=phone)

    def query_id(self, query_id):
        try:
            return self.get(query_id=query_id)
        except Exception as e:
            # setting error messages for user nad developer respectively
            field_message = "Server Error. Contact Customer Support."
            for_developer = f"{e}"

            # Raising error responses
            response.errors(field_error=field_message,
                            for_developer=for_developer,
                            code="BAD_REQUEST", status_code=400)


class VerifyUserManager(UserManager):

    def user_exists(self, query_id: str) -> bool:
        """
        checks if user exists using query id
        """
        try:
            self.get(query_id=query_id)
        except ObjectDoesNotExist:
            return False
        return True

    def email_exists(self, email: str) -> bool:
        """
        Checks if email exists
        """
        try:
            self.get(email=email)
        except ObjectDoesNotExist:
            return False
        return True

    def phone_exists(self, phone: str) -> bool:
        """
        Checks If Phone Exists
        """
        try:
            self.get(phone=phone)
        except ObjectDoesNotExist:
            return False
        return True

    def username_exists(self, username: str) -> bool:
        """
        Checks if username exists
        """
        try:
            self.get(username=username)
        except ObjectDoesNotExist:
            return False
        return True
