import re, json

from django.db import models
from django.core.validators import validate_email
from django.core.exceptions import ValidationError

from accounts.models.users import User

from utilities import response

"""
Field validation functions returns a tuple
1) tuple[0] = validation boolean value (True, False)
2) tuple[1] = validation code
3) tuple[2] = validation status code

Maintain the validation code and validation status code.
They'll be used to carry out checks in different files.
Changing the values requires doing the change everywhere else
"""

class UsernameValidation:
    def __init__(self, username: str, uniqueness: bool = True, pattern: bool = True):
        self.username = username
        self.uniqueness = uniqueness
        self.pattern = pattern

    def validate_uniqueness(self) -> tuple:

        if User.verify.username_exists(self.username):
            return False, "USERNAME_CONFLICT", 409
        return True, "USERNAME_ACCEPTED", 202
    
    def validate_pattern(self) -> tuple:

        min_length = 6
        max_length = 15
        # Regex pattern for usernames (letters and digits only, no spaces or special characters)
        # ^ asserts the start of the string
        # [a-zA-Z0-9] matches any letter (uppercase or lowercase) or digit
        # {min_length,max_length} specifies the minimum and maximum length
        # $ asserts the end of the string
        regex_pattern = r"^[a-zA-Z0-9]{" + str(min_length) + "," + str(max_length) + "}$"

        # Compile the regex pattern
        pattern = re.compile(regex_pattern)

        if pattern.match(self.username):
            return True, "VALID_USERNAME", 202
        else:
            return False, "INVALID_USERNAME", 400
    
    def validate(self) -> tuple:
        criterions = [self.validate_uniqueness, self.validate_pattern]

        # Unpack the results of each criterion
        results = [criterion for criterion in criterions]

        # Check if all functions in criterions return True using all()
        if all(result[0] for result in results):
            return True, "VALID_USERNAME", 202
        else:
            failed_criteria = [result for result in results if not result[0]]

            # You can inspect the failed criteria here
            failed_messages = [message for _, message, _ in failed_criteria]
            return False, "INVALID_USERNAME", 400


class EmailValidation:
    """
    ----> Used in:
               1) User serializer (accounts/serializers/users [UserSerializer])
    """
    def __init__(self, email: str, uniqueness: bool = True, pattern: bool = True):
        self.email = email
        self.uniqueness = uniqueness
        self.pattern = pattern
    
    def validate_uniqueness(self) -> tuple:
        if User.verify.email_exists(self.email):
            return False, "EMAIL_CONFLICT",  409, f"User With This Email ({self.email}) Already Exists"
        return True, "EMAIL_ACCEPTED", 202, f"This Email ({self.email}) Is Unique"
    
    def validate_pattern(self) -> tuple:
        # Regular expression pattern for a basic email address validation
        # regex_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"

        try:
            validate_email(self.email)
        except ValidationError as e:
            return False, "INVALID_EMAIL", 400, str(e)
        
        return True, "VALID_EMAIL", 202, f"This Email Address ({self.email}) Is Valid"

        # # Compile the regex pattern
        # pattern = re.compile(regex_pattern)

        # if pattern.match(self.email):
        #     return True, "VALID_EMAIL", 202, None
        # else:
        #     return False, "INVALID_EMAIL", 400, None

    def validate(self) -> tuple:

        if self.uniqueness:
            result_uniqueness = self.validate_uniqueness()

            if not self.pattern:
                # Checks if the boolean value is False
                if not result_uniqueness[0]:
                    return result_uniqueness

        if self.pattern:
            result_pattern = self.validate_pattern()

            if not self.uniqueness:
                if not result_pattern[0]:
                    return result_pattern
        
        if self.uniqueness and self.pattern:

            if not result_uniqueness[0] and not result_pattern[0]:
                result_message = [result_uniqueness[3], result_pattern[3]]

                return False, "INVALID", 409, result_message
            
            if result_uniqueness[0] and result_pattern[0]:

                # If None of the functions return boolean value False
                return True, "EMAIL_ACCEPTED", 202, f"Acceptable Email Address ({self.email})"
    
    def validate_or_raise(self) -> str:

        email_validation = self.validate()

        if not email_validation[0]:
            if email_validation[1] == 'EMAIL_CONFLICT':
                field_message = "User With This Email Already Exists"
            
            elif email_validation[1] == "INVALID_EMAIL":
                field_message = "Invalid Email Pattern. Example email: johndoe@email.com"
            
            else:
                for_developer = email_validation[3]

            # raising error responses
            response.errors(field_error=field_message, for_developer=for_developer, code=email_validation[1], 
                            status_code=email_validation[2])
            
        return self.email


class PhoneValidation:
    def __init__(self, phone: str, uniqueness: bool = True, pattern: bool = True):
        self.phone = phone
        self.uniqueness = uniqueness
        self.pattern = pattern

    def validate_uniqueness(self) -> tuple:
        if User.verify.phone_exists(self.phone):
            return False, "PHONE_CONFLICT", 409
        return True, "PHONE_ACCEPTED", 202
    
    def validate_pattern(self) -> tuple:
        # Regular expression pattern for a basic phone number address validation
        regex_pattern = r"^\+[0-9]{7,15}$"

        # Compile the regex pattern
        pattern = re.compile(regex_pattern)

        if pattern.match(self.phone):
            return True, "VALID_PHONE", 202
        else:
            return False, "INVALID_PHONE", 400
    
    def validate(self) -> tuple:

        if self.uniqueness:
            result_uniqueness = self.validate_uniqueness()

            # Checks if the boolean value is False
            if not result_uniqueness[0]:
                return result_uniqueness

        if self.pattern:
            result_pattern = self.validate_pattern()

            if not result_pattern[0]:
                return result_pattern

        # If None of the functions return boolean value False
        return True, "PHONE_ACCEPTED", 202
    
    def validate_or_raise(self) -> str:

        phone_validation = self.validate()

        if not phone_validation[0]:
            if phone_validation[1] == 'PHONE_CONFLICT':
                field_message = "User With This Phone Already Exists"
                for_developer = "User With This Phone Already Exists"
            
            elif phone_validation[1] == "INVALID_PHONE":
                field_message = "Invalid Phone Pattern. Example phone number: +123456789034765"
                for_developer = "Invalid Phone Pattern. Example phone number: +123456789034765"

            # raising error responses
            response.errors(field_error=field_message, for_developer=for_developer, code=phone_validation[1], 
                            status_code=phone_validation[2])
            
        return self.phone


class PasswordValidation:
    def __init__(self, password: str, user: dict = {}, similarity: bool = True, strength: bool = True):
        self.password = password
        self.user = user
        self.similarity = similarity
        self.strength = strength

    def validate_similarity(self) -> tuple:

        if self.user == {}:
            # Check if the password contains any substrings of the user's information (username, email, phone number)
            for info in self.user.values():
                if info and str(info).lower() in self.password.lower():
                    return False, "PASSWORD_BAD_REQUEST", 400
        return True, "PASSWORD_ACCEPTED", 202

    def validate_strength(self) -> tuple:
        # Define password strength criteria
        criteria = [
            (len(self.password) >= 12, "Password must be at least 12 characters long", 400),
            (re.search(r'[A-Z]', self.password), "Password must contain at least one uppercase letter", 400),
            (re.search(r'[a-z]', self.password), "Password must contain at least one lowercase letter", 400),
            (re.search(r'\d', self.password), "Password must contain at least one digit", 400),
            (re.search(r'[!@#$%^&*()_+{}\":<>?]', self.password), "Password must contain at least one special character", 400)
        ]

        failed_criteria = [(message, status_code) for condition, message, status_code in criteria if not condition]

        if not failed_criteria:
            return True, "PASSWORD_ACCEPTED", 202
        else:
            error_messages = [message for message, _ in failed_criteria]
            return False, "NOT_ACCEPTABLE", 406

    def validate(self) -> tuple:

        if self.similarity:
            password_similarity = self.validate_similarity()

            if not password_similarity[0]:
                return password_similarity
        
        if self.strength:
            password_strength = self.validate_strength()

            if not password_strength[0]:
                return password_strength
        
        return True, "PASSWORD_ACCEPTED", 202
    
    def validate_or_raise(self):

        password_validation = self.validate()
        if not password_validation[0]:
            if password_validation[1] == "PASSWORD_BAD_REQUEST":
                field_message = "Password Is Similar To User Information"
                for_developer = "Password Is Similar To User Information"
            
            elif password_validation[1] == "NOT_ACCEPTABLE":
                field_message = "Password Must Contain Atleast: 12 Characters, 1 Uppercase and Lowercase, 1 Digit and 1 Special Character And Must Not Be Similar To Any Of Your User's Information"
                for_developer = "Password Must Contain Atleast: 12 Characters, 1 Uppercase and Lowercase, 1 Digit and 1 Special Character And Must Not Be Similar To Any Of Your User's Information"
            
            # Raising error responses
            response.errors(field_error=field_message, for_developer=for_developer, code=password_validation[1], 
                            status_code=password_validation[2])
            
        return self.password