from celery import shared_task
from django.core.mail import send_mail

@shared_task
def send_email_task(subject, message, recipient):
    send_mail(
        subject,
        message,
        'no-reply@johnsonelectric.com',  
        [recipient],  # Send to one recipient at a time
        fail_silently=False,
    )
