from django.core.management.base import BaseCommand
from django.utils import timezone
from accounts.models.account import PhoneNumberVerificationOTP, EmailVerificationOTP
from django.conf import settings
from utilities.tasks import send_email_task, send_sms_task


class Command(BaseCommand):
    help = ('Deletes unverified accounts created n days ago'
            ' and sends notification emails')

    def add_arguments(self, parser):
        parser.add_argument(
            '--days', type=int,
            help='Specify the number of days to consider for cleanup'
        )
        parser.add_argument(
            '--secret-key', help='Secret key for authentication'
        )

    def handle(self, *args, **options):
        secret_key = options.get('secret_key')
        inactive_days = options.get('days')
        expected_secret_key = settings.APPLICATION_SETTINGS["CMD_SECRET_KEY"]

        if secret_key != expected_secret_key or not expected_secret_key:
            self.stdout.write(
                self.style.ERROR('Invalid secret key. Access denied.')
            )
            return

        cutoff_datetime = timezone.now() - (
            timezone.timedelta(days=inactive_days)
            if inactive_days
            else settings.APPLICATION_SETTINGS['INACTIVITY_LIMIT']
        )

        # Query inactive users with phone verification setup
        inactive_phoneusers = PhoneNumberVerificationOTP.objects.filter(
            current_otp__isnull=False, user__datetime_joined__lt=cutoff_datetime
        )
        phone_recipient_list = [
            user.user.phone for user in inactive_phoneusers if user.user.delete()[0] > 0
        ]

        # Query inactive users with email verification setup
        inactive_emailusers = EmailVerificationOTP.objects.filter(
            current_otp__isnull=False, user__datetime_joined__lt=cutoff_datetime
        )
        email_recipient_list = [
            user.user.email for user in inactive_emailusers if user.user.delete()[0] > 0
        ]

        # Send email notifications
        send_email_task.delay(
            subject="LaLouge | (Unverified) Account Deleted",
            message="Unable to verify account. Account Deleted!",
            recipient_list=email_recipient_list,
        )

        # Send SMS notifications
        send_sms_task.delay(
            sub_id="Deleted (Unverified) Account",
            message="Your LaLouge inactive account has been automatically deleted.",
            phone=phone_recipient_list,
        )

        self.stdout.write(
            self.style.SUCCESS(
                (f'Successfully deleted unverified accounts.'
                 f' created before {cutoff_datetime.ctime()}')
            )
        )
