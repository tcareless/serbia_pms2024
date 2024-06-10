import random
from django.core.mail import send_mail
from django.conf import settings

EMAIL_SUBJECT_TEMPLATE = 'Unlock Code: {code}'

def get_combined_email_groups(*group_names):
    email_list = []
    for group_name in group_names:
        email_list.extend(settings.EMAIL_GROUPS.get(group_name, []))
    return email_list

def generate_unlock_code():
    return '{:03d}'.format(random.randint(0, 999))

def send_unlock_code_email(code):
    subject_with_code = EMAIL_SUBJECT_TEMPLATE.format(code=code)
    email_list = get_combined_email_groups(
        'Testing_group',
    )
    try:
        send_mail(
            subject_with_code,
            f'The new unlock code is: {code}',
            settings.DEFAULT_FROM_EMAIL,
            email_list,
            fail_silently=False,
        )
        print("Email sent successfully.")
    except Exception as e:
        print(f"Error sending email: {e}")

def generate_and_send_code():
    code = generate_unlock_code()
    send_unlock_code_email(code)
    return code
