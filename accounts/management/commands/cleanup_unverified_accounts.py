# app/management/commands/cleanup_unverified_accounts.py

from django.core.management.base import BaseCommand
from django.utils import timezone
from accounts.models.account import PhoneNumberVerificationOTP, EmailVerificationOTP
from django.conf import settings
from datetime import timedelta


from utilities.tasks import send_email_task, send_sms_task


class Command(BaseCommand):
    help = 'Deletes unverified accounts created n days ago and sends notification emails'

    def add_arguments(self, parser):
        parser.add_argument('--days', type=int, help='Specify the number of days to consider for cleanup')

        # Implementing A Secret Key (Password) Argument
        parser.add_argument('--secret-key', help='Secret key for authentication')

    def handle(self, *args, **options):

        # Checking If Secret Key Works
        secret_key = options.get('secret_key')
        inactive_days = options.get('days')

        # Getting Command Prompt Actual Secret Key From APPLICATION SETTINGS In `settings.py`
        expected_secret_key = settings.APPLICATION_SETTINGS["CMD_SECRET_KEY"]

        if secret_key != expected_secret_key or expected_secret_key is None:
            self.stdout.write(self.style.ERROR('Invalid secret key Or Secret Key Not Found. Access denied.'))
            return

        
        cutoff_datetime = timezone.now() - (timezone.timedelta(days=inactive_days) if inactive_days else settings.APPLICATION_SETTINGS['INACTIVITY_LIMIT'])

        # Querying Inactive Users With Phone Verification Setup
        inactive_users = PhoneNumberVerificationOTP.objects.filter(
            current_otp__isnull=False, user__datetime_joined__lt=cutoff_datetime
        )

        phone_recipient_list = []
        for inactive_user in inactive_users:
            
            is_deleted = inactive_user.user.delete()
            
            # Checking If The User Account Has Successfully Been Deleted
            if is_deleted[0] > 0:

                # Appending Inactive User's Phone Number To Phone Recipient List
                phone_recipient_list.append(inactive_user.user.phone)
        
        # Querying Inactive Users With Email Verification Setup
        inactive_users = EmailVerificationOTP.objects.filter(
            current_otp__isnull=False, user__datetime_joined__lt=cutoff_datetime
        )

        email_recipient_list = []
        for inactive_user in inactive_users:

            # Deleting Inactive User From Database
            is_deleted = inactive_user.user.delete()

            # Checking If The User Account Has Successfully Been Deleted
            if is_deleted[0] > 0:

                # Appending Inactive User's Email To Email Recipient List
                email_recipient_list.append(inactive_user.user.email)
        
        # Sending Email Messages To Users Whose Unverified Accounts Has Just Been Deleted
        subject = "LaLouge | (Unverified) Account Deleted"

        message = "Account deleted because you've been unable to verify account"

        send_email_task.delay(subject=subject, message=message, recipient_list=email_recipient_list)

        # Sending Phone Messages To User's Whose Unverified Accounts Has Just Been Deleted
        message = f"Your LaLouge Inactive Account Has Been Automatically Deleted"

        sub_id = "Deleted (Unverified) Account"
        
        send_sms_task.delay(sub_id=sub_id, message=message, phone=phone_recipient_list)
        
        self.stdout.write(self.style.SUCCESS(f'Successfully deleted unverified accounts created before the {cutoff_datetime.ctime()}'))

