import random
from django.core.mail import send_mail
from django.conf import settings

EMAIL_SUBJECT = 'Subject of email'
EMAIL_LIST = ['tyler.careless@johnsonelectric.com']

def generate_unlock_code():
    return '{:03d}'.format(random.randint(0, 999))

def send_unlock_code_email(code):
    try:
        send_mail(
            EMAIL_SUBJECT,
            f'The new unlock code is: {code}',
            settings.DEFAULT_FROM_EMAIL,
            EMAIL_LIST,
            fail_silently=False,
        )
        print("Email sent successfully.")
    except Exception as e:
        print(f"Error sending email: {e}")

def generate_and_send_code():
    code = generate_unlock_code()
    send_unlock_code_email(code)
    return code
