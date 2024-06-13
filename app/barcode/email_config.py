import random
from django.core.mail import send_mail
from django.conf import settings

# Template for the email subject, including a placeholder for the unlock code
EMAIL_SUBJECT_TEMPLATE = 'Unlock Code: {code}'

def get_combined_email_groups(*group_names):
    email_list = []
    for group_name in group_names:
        # Extend the email list with addresses from the specified groups
        email_list.extend(settings.EMAIL_GROUPS.get(group_name, []))
    return email_list



def generate_unlock_code():
    """
    Generates a random 3-digit unlock code.
    """
    return '{:03d}'.format(random.randint(0, 999))



def send_unlock_code_email(code):
    """
    Sends an email containing the unlock code to a specified group of recipients.
    """
    subject_with_code = EMAIL_SUBJECT_TEMPLATE.format(code=code)
    # Get the email list from the 'Testing_group', add more groups from settings.py EMAIL_GROUPS if you'd like.
    email_list = get_combined_email_groups('Testing_group', 'Factory_Focus_Leaders', 'Supervisor_Leads', 'Supervisors', 'Backup_Supervisors', 'Team_Leads', 'Quality')
    try:
        # Send the email with the unlock code
        send_mail(
            subject_with_code,
            f'The new unlock code is: {code}',
            settings.DEFAULT_FROM_EMAIL,
            email_list,
            fail_silently=False,
        )
        print("Email sent successfully.")
    except Exception as e:
        # Print the error message if email sending fails
        print(f"Error sending email: {e}")

        

def generate_and_send_code():
    """
    Generates a new unlock code and sends it via email.
    
    Returns:
        The generated unlock code.
    """
    code = generate_unlock_code()
    send_unlock_code_email(code)
    return code
