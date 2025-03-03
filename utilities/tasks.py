# your_app/tasks.py
from celery import shared_task

from django.core.management import call_command
from django.conf import settings

from typing import Union, List

import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException

from utilities import response

import json
import requests


@shared_task
def send_email_task(
    html_content: str, user_pk: int,
    recipient_list: Union[str, list[str]],
    sender: dict[str, str], subject: str
):

    print("DID IT GET HERE ???")

    # Configure API key authorization
    configuration = sib_api_v3_sdk.Configuration()
    configuration.api_key['api-key'] = settings.BREVO_SETTINGS['BREVO_API_KEY']

    # Create an instance of the Email API
    api_instance = sib_api_v3_sdk.TransactionalEmailsApi(
        sib_api_v3_sdk.ApiClient(configuration)
    )

    # Create the email data
    email = sib_api_v3_sdk.SendSmtpEmail(
        to=recipient_list,  # Specify recipients
        sender=sender,  # Specify sender
        subject=subject,  # Email subject
        html_content=html_content,  # Rendered HTML template
    )

    try:
        print("TRY TRY TRY TRY")
        # Send the email
        answer = api_instance.send_transac_email(email)
        print("ANSWER:\n", answer)
    except ApiException as e:
        print("ERROR ERROR ERROR")
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

    # Converting Phone To A List String Of Single
    # Element If Phone Is A String

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

        requests.request("POST", url, headers=headers, data=payload)


@shared_task
def clean_up_unverified_accounts():

    # Calling The Cleanup_unverified_accounts Management
    # Command And Parsing The CMD_SECRET_KEY (Password) To It
    # Found IN accounts.management.commands.cleanup_unverified_accounts.py
    call_command(
        'cleanup_unverified_accounts',
        '--secret-key',
        settings.APPLICATION_SETTINGS['CMD_SECRET_KEY']
    )
