from accounts.models.users import User
from accounts.models.profiles import UserProfile
from accounts.models.devices import Device
from accounts.models.account import (
    PhoneNumberVerificationOTP, EmailVerificationOTP, LoginOTP,
    UsedOTP, OTPModels, AccountVerification)

from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.db import models
from django.conf import settings

from rest_framework_simplejwt.tokens import RefreshToken

from utilities import response
from utilities.models.relationship_checker import ModelRelationshipChecker
from utilities.tasks import send_email_task, send_sms_task


class Verification:
    def __init__(self, user: User, model: models.Model = PhoneNumberVerificationOTP,
                 check_verification: bool = False):
        self.user = user
        self.model = model
        self.check_verification = check_verification

    def get_legal_name(self, user):
        try:
            user_profile = UserProfile.objects.get(user=user)
        except UserProfile.DoesNotExist:
            return None

        return user_profile.legal_name

    def send_via_email(self, model_otp_instance: models.Model = None):

        if model_otp_instance is not None:

            otp_code = model_otp_instance.current_otp.otp

            # Load and render the template
            context = {
                "otp": otp_code  # Pass dynamic data for the template
            }
            html_content = render_to_string("email/email-verification.html", context)

            # Get the recipient's name (legal name or fallback to username)
            legal_name = self.get_legal_name(self.user)
            recipient_name = legal_name if legal_name else self.user.username

            recipient_list = [
                {
                    "email": self.user.email,
                    "name": recipient_name
                }
            ]

            brevo_settings = settings.BREVO_SETTINGS

            sender = {
                "email": brevo_settings["SENDER_EMAIL"]["NO_REPLY"]["email"],
                "name": brevo_settings["SENDER_EMAIL"]["NO_REPLY"]["name"]
            }

            subject = "Verify Your Account - LaLouge"

            try:
                send_email_task.delay(
                    html_content=html_content,
                    user_pk=self.user.pk,
                    otp_code=otp_code,
                    recipient_list=recipient_list,
                    sender=sender,
                    subject=subject
                )
            except Exception as e:
                # setting error messages for user and developer respectively
                field_message = "Failed To Send Email For Verification"
                for_developer = str(e)

                # Raising error responses
                response.errors(
                    field_error=field_message,
                    for_developer=for_developer,
                    code="SERVER_ERROR",
                    status_code=1011,
                    main_thread=False,
                    param=self.user.pk
                )

        else:
            # setting error messages for user and
            # developer respectively
            field_message = "Failed To Send SMS For Verification"
            for_developer = "Unable To Read Model Instance Assigned To User"
            # Raising error responses
            response.errors(
                field_error=field_message,
                for_developer=for_developer,
                code="SERVER_ERROR",
                status_code=1011,
                main_thread=False,
                param=self.user.pk
            )

    def send_via_sms(self, model_otp_instance: models.Model = None):

        if model_otp_instance is not None:
            sub_id = "Verify Phone Number"

            message = f"OTP {model_otp_instance.current_otp.otp}"

            try:
                send_sms_task.delay(
                    sub_id=sub_id, message=message, phone=self.user.phone
                )
            except Exception as e:
                # setting error messages for user and developer respectively
                field_message = "Failed To Send SMS For Verification"
                for_developer = str(e)

                # Raising error responses
                response.errors(
                    field_error=field_message,
                    for_developer=for_developer,
                    code="SERVER_ERROR",
                    status_code=1011,
                    main_thread=False,
                    param=self.user.pk)

        else:
            # setting error messages for user and developer respectively
            field_message = "Failed To Send SMS For Verification"
            for_developer = "Unable To Read Model Instance Assigned To User"
            # Raising error responses
            response.errors(
                field_error=field_message,
                for_developer=for_developer,
                code="SERVER_ERROR",
                status_code=1011,
                main_thread=False,
                param=self.user.pk
            )

    def send_code_to_user(self, model_instance: models.Model):

        is_valid, model_otp_instance = self._check_generated_code_existence()

        if is_valid:

            phone_otp_model_name = PhoneNumberVerificationOTP._meta.model_name
            email_otp_model_name = EmailVerificationOTP._meta.model_name
            login_otp_model_name = LoginOTP._meta.model_name

            if model_instance._meta.model_name == phone_otp_model_name:
                self.send_via_sms(model_otp_instance=model_otp_instance)

            elif model_instance._meta.model_name == email_otp_model_name:
                self.send_via_email(model_otp_instance=model_otp_instance)

            elif model_instance._meta.model_name == login_otp_model_name:
                if self.user.email:
                    self.send_via_email(model_otp_instance=model_otp_instance)
                else:
                    self.send_via_sms(model_otp_instance=model_otp_instance)

    def _check_generated_code_existence(self):
        try:
            # Please, note: model_otp_instance is the
            # model instance belonging
            # to a particular user. I'm unable to think of a
            # suitable variable name for it

            model_otp_instance = self.model.objects.get(user=self.user)
        except self.model.DoesNotExist:
            field_message = "OTP Was Not Created For This User"
            for_developer = (
                f"""OTP For Corresponding Model"
                " ({self.model}) Was Not Created For User"
                " ({self.user.name})"""
            )

            # Raising error responses
            response.errors(
                field_error=field_message,
                for_developer=for_developer,
                code="SERVER_ERROR",
                status_code=1011,
                main_thread=False,
                param=self.user.pk
            )

        return True, model_otp_instance

    def email(self, send_code: bool = True) -> bool:

        if not self.check_verification:

            self.send_code_to_user(model_instance=self.model)

    def phone(self) -> bool:

        self.send_code_to_user(model_instance=self.model)


class CheckVerifiedCredentials:
    """
        This checks if the various user credentials has been verified.
        It follows the hierachal order
        Phone Number Verification
        Email Verification
        Device Validity which starts from 30% Trust to The existence
        Of the Device Token To A Valid Device Name
        Then Extras Such As KYC
    """
    def __init__(self, user_instance: User):
        self.user = user_instance

    def is_phone_email_verified(self, check_device=False, **kwargs):
        device_check = ["device", None]

        if check_device:
            user_device_instances = Device.objects.filter(user=self.user)

            if user_device_instances.exists():
                # Getting The Latest Device Instance From List Of User Devices
                user_last_device_instance = user_device_instances.last()

                if user_last_device_instance._is_trusted > 30:
                    if user_last_device_instance._device_token is not None:
                        if user_last_device_instance.device_name is not None:
                            device_check[0] = user_last_device_instance.device_name
                            device_check[1] = True

                        else:
                            device_check[1] = False

                    else:
                        device_check[1] = False

                else:
                    device_check[1] = False

        phone_status = ["phone", self.is_phone_Verified()]
        email_status = ["email", self.is_email_Verified()]
        return phone_status, email_status, device_check

    def is_email_verified(self):
        try:
            account_verification_instance = AccountVerification.objects.get(
                user=self.user
            )
        except (AccountVerification.DoesNotExist, Exception):
            return False

        if account_verification_instance.email_verified:
            return True
        else:
            return False

    def is_phone_verified(self):
        try:
            account_verification_instance = AccountVerification.objects.get(
                user=self.user
            )
        except (AccountVerification.DoesNotExist, Exception):
            return False

        if account_verification_instance.phone_number_verified:
            return True
        else:
            return False


class OTP:
    def __init__(
            self, otp: str = None, user: User = None,
            model: models.Model = PhoneNumberVerificationOTP,
            database_actions=True, send_update=True
    ):

        self.otp = otp
        self.user = user
        self.model = model
        self.database_actions = database_actions
        self.send_update = send_update

    def is_valid(self):

        if self.otp is None or self.user is None:
            # Raising errors
            response.errors(
                field_error="Internal Server Error. Contact Support.",
                for_developer=(
                    f"""`otp` And/Or `user` Attribute Value
                     in {self} Should Not Be None."""
                ),
                code="INTERNAL_SERVER_ERROR",
                status_code=500
            )

        # Checking model validity
        if not self._check_model_validity():
            # Raising errors
            response.errors(
                field_error="Invalid Model",
                for_developer=(
                    f"""Model ({self.model._meta.model_name})
                     Not A Valid Model For This Operation.
                     Valid Models Are {dir(OTPModels)}"""
                ),
                code="INTERNAL_SERVER_ERROR",
                status_code=500
            )

        model_instances = self.model.objects.filter(user=self.user)

        if not model_instances.exists():
            # setting error messages for user and
            # developer respectively

            field_message = "Internal Server Error. Contact Support"
            for_developer = (
                f"""{self.user} Is Not Attributed To Any
                 {self.model._meta.model_name}. Probably Error Occured
                 During Creation Of User Process Or A Dev Must Have
                 Tampered With The GenerateOTP Function In
                 utilities/generators/otp.py"""
            )

            # Raising error responses
            response.errors(
                field_error=field_message,
                for_developer=for_developer,
                code="INTERNAL_SERVER_ERROR",
                status_code=500
            )

        elif model_instances.count() > 1:
            # setting error messages for user and
            # developer respectively

            field_message = "Internal Server Error. Contact Support"
            for_developer = (
                f"""{self.user} Is Attributed To More Than One
                {self.model._meta.model_name}. Check User Model
                Relationship With {self.model._meta.model_name},
                It Must Be A OneToOne Relationship Else You'll Keep
                Receiving This Error"""
            )

            # Raising error responses
            response.errors(
                field_error=field_message,
                for_developer=for_developer,
                code="SERVER_ERROR",
                status_code=500
            )

        # Avoiding QuerySet Value Instance
        model_instance = model_instances.first()

        if model_instance.current_otp:
            if not self.database_actions:
                return self.otp == model_instance.current_otp.otp

            if self.otp and self.otp != model_instance.current_otp.otp:
                return False
        else:
            return False

        if self.database_actions:
            self.perform_database_actions(
                model_instance=model_instance
            )

        if self.send_update:
            try:
                send_sms_task.delay(
                    sub_id="Verify Phone Number",
                    message="Congratulations. Phone Number Verified",
                    phone=self.user.phone
                )
            except Exception as e:
                # setting error messages for user and
                # developer respectively

                field_message = "Failed To Send SMS For Verification"
                for_developer = str(e)

                # Raising error responses
                response.errors(
                    field_error=field_message,
                    for_developer=for_developer,
                    code="BAD_REQUEST",
                    status_code=400
                )

        return True

    def perform_database_actions(self, model_instance):
        otp_instance = model_instance.current_otp

        check_relationship = self._relationship_checker()

        if (
            check_relationship[0]
            and check_relationship[2] == models.ForeignKey.__name__
        ):
            field_name = check_relationship[1]

        else:
            # Raising errors
            response.errors(
                field_error="Relationship Nonexistent",
                for_developer=(
                    f"""Model ({self.model._meta.model_name})
                     Has No Relationship With {OTP._meta.model_name}
                     or Model ({self.model._meta.model_name}) Is Not
                     A ForeignKey To {OTP._meta.model_name}"""
                ),
                code="BAD_REQUEST",
                status_code=400
            )

        # Creating a dictionary with the dynamic
        # field name and value
        update_dict = {
            "otp": otp_instance,
            field_name: model_instance
        }

        # Updating instances based on the dynamic field name
        UsedOTP.objects.filter(
            **update_dict
        ).update(is_active=False)

        model_instance.current_otp = None
        model_instance.save()

        # Creating Or Updating Account Verification Model

        account_verification_instance = AccountVerification.objects.get(
            user=self.user
        )

        if self.model == PhoneNumberVerificationOTP:
            account_verification_instance.phone_number_verified = True
        elif self.model == EmailVerificationOTP:
            account_verification_instance.email_verified = True

        account_verification_instance.save()

        return

    def _check_model_validity(self):
        return any(
            isinstance(
                self.model,
                getattr(OTPModels, model_name)
            ) for model_name in dir(OTPModels)
        )

    def _relationship_checker(self):
        checker = ModelRelationshipChecker()
        has_relationship, field_name, relationship_type = checker.check_relationship(
            target_model_name=self.model._meta.model_name,
            potential_relationship_model_name='UsedOTP',
            app_label=self.model._meta.app_label,
            relationship_type=models.ForeignKey
        )

        return has_relationship, field_name, relationship_type


class Password:
    def __init__(self, user: User):
        self.user = user

    def reset(self) -> bool:
        redirect_url = "hello"

        refresh = RefreshToken.for_user(self.user)
        reset_password_token = urlsafe_base64_encode(
            force_bytes(
                f"{self.user.pk}-{str(refresh.access_token)}"
            )
        )

        # using the value of the `absolute_uri` value
        # to create the referral link
        reset_password_url = (
            f"""{redirect_url}?reset-password-token=
            {reset_password_token}"""
        )

        # Send email with reset password link
        subject = 'Password reset'

        message = render_to_string(
            'email/forgot-password.html', {
                'reset_password_url': reset_password_url
            }
        )

        from_email = "ramsesnjasap11@example.com"
        recipient_list = [self.user.email]

        try:
            send_mail(
                subject,
                message,
                from_email,
                recipient_list,
                html_message=message
            )
        except Exception as e:

            # setting error messages for user and
            # developer respectively

            field_message = "Failed To Send Email For Verification"
            for_developer = str(e)

            # Raising error responses
            response.errors(
                field_error=field_message,
                for_developer=for_developer,
                code="BAD_REQUEST",
                status_code=400
            )
