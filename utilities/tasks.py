# your_app/tasks.py
from accounts.models.users import User
from accounts.models.account import PhoneNumberVerificationOTP, EmailVerificationOTP

from celery import shared_task

from django.core.mail import send_mail
from django.core.management import call_command
from django.utils import timezone
from django.conf import settings

from utilities import response

from typing import Union, List

import json, requests
from django.core.mail import EmailMessage


@shared_task
def send_email_task(template_id: int, user_pk: int, otp_code: int, recipient_list: Union[str, list[str]]):

    recipient_lists = [recipient_list] if isinstance(recipient_list, str) else recipient_list

    for recipient_list in recipient_lists:

        message = EmailMessage(to=[recipient_list])
        message.template_id = template_id
        message.from_email = None
        message.merge_global_data = {
            "otp": otp_code,
        }
        try:
            message.send()
        except Exception as e:
            response.errors(
                field_error="Failure To Send Verification Email",
                for_developer=str(e),
                code="SERVER_ERROR",
                status_code=1011,
                main_thread=False,
                param=user_pk
            )


@shared_task
def send_sms_task(sub_id: str, message: str, phone: Union[str, List[str]]):

    url = "https://smsvas.com/bulk/public/index.php/api/v1/sendsms/"

    # Converting Phone To A List String Of Single Element If Phone Is A String

    phone_numbers = [phone] if isinstance(phone, str) else phone

    for single_phone in phone_numbers:

        payload = json.dumps({
            "user": settings.SMS_USER,
            "password": settings.SMS_PASSWORD,
            "senderid": f"LaLouge - {sub_id}",
            "sms": message,
            "mobiles": str(single_phone).replace("+", "")
        })
        headers = {
        'Content-Type': 'application/json'
        }

        requests.request("POST", url, headers=headers, data=payload, timeout=60)


@shared_task
def clean_up_unverified_accounts():

    # Calling The Cleanup_unverified_accounts Management Command And Parsing The CMD_SECRET_KEY (Password) To It
    # Found IN accounts.management.commands.cleanup_unverified_accounts.py
    call_command('cleanup_unverified_accounts', '--secret-key', settings.APPLICATION_SETTINGS['CMD_SECRET_KEY'])
