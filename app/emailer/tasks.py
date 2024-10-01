from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings

@shared_task
def send_email_task(to_emails, subject, message, html_message, from_email):
    send_mail(
        subject,
        message,  # Plain text version of the message (can be an empty string)
        from_email,  # Use the provided sender email
        to_emails,
        html_message=html_message  # HTML version of the message
    )
