import random
from django.core.mail import send_mail
from django.conf import settings

# Template for the email subject, including a placeholder for the unlock code
EMAIL_SUBJECT_TEMPLATE = 'Duplicate Scanned at AB1V/10R140 Unlock Code:{code}'

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

def send_unlock_code_email(code, barcode, scan_time):
    """
    Sends an email containing the unlock code and detailed instructions to a specified group of recipients.
    """
    subject_with_code = EMAIL_SUBJECT_TEMPLATE.format(code=code)
    email_list = get_combined_email_groups('Testing_group', 'Factory_Focus_Leaders', 'Supervisor_Leads', 'Supervisors', 'Backup_Supervisors', 'Team_Leads', 'Quality')
    # email_list = get_combined_email_groups('Testing_group')

    email_body = f"""
    <p>A duplicate part has been scanned at AB1V or 10R140 100% inspection table.</p>

    <p><strong>{barcode}</strong> was previously scanned at <strong>{scan_time}</strong>.</p>

    <p>You need to go to the station and investigate:</p>

    <p>If the first scan occurred more than 15 minutes ago (Is it likely to still be at the station?):</p>
    <ul>
        <li>Scrap the part in question</li>
        <li>Unlock the station and the operators can resume normal production</li>
    </ul>

    <p>If the first scan occurred less than 15 minutes ago:</p>
    <ul>
        <li>Have the operator go back through the skid and see if there was indeed a duplicate part</li>
        <li>If a duplicate is found, take both parts, Red Tag them and send to QA for investigation.</li>
        <li>If it is determined that the operator scanned the same part twice, unlock the station and the operators can resume normal production.</li>
    </ul>

    <p style="font-size: 24px; font-weight: bold; color: #1976D2;">Unlock Code: {code}</p>
    """
    try:
        # Send the email with the detailed instructions and unlock code
        send_mail(
            subject_with_code,
            '',
            settings.DEFAULT_FROM_EMAIL,
            email_list,
            fail_silently=False,
            html_message=email_body,
        )
        print("Email sent successfully.")
    except Exception as e:
        # Print the error message if email sending fails
        print(f"Error sending email: {e}")

def generate_and_send_code(barcode, scan_time):
    """
    Generates a new unlock code and sends it via email with the provided barcode and scan time information.
    
    Returns:
        The generated unlock code.
    """
    code = generate_unlock_code()
    send_unlock_code_email(code, barcode, scan_time)
    return code
