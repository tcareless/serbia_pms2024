# barcode/tasks.py

from celery import shared_task
from email.mime.text import MIMEText
import smtplib

# Define your email groups here
EMAIL_GROUPS = {
    'Managers': [
        'dave.milne@johnsonelectric.com',
        'joel.langford@johnsonelectric.com',
        'dave.clark@johnsonelectric.com',
    ],
    'Supervisor_Leads': [
        'ken.frey@johnsonelectric.com',
        'brian.joiner@johnsonelectric.com',
        'gary.harvey@johnsonelectric.com',
    ],
    'Supervisors': [
        'andrew.smith@johnsonelectric.com',
        'saurabh.bhardwaj@johnsonelectric.com',
        'paul.currie@johnsonelectric.com',
        'andrew.terpstra@johnsonelectric.com',
        'evan.george@johnsonelectric.com',
        'david.mclaren@johnsonelectric.com',
        'robert.tupy@johnsonelectric.com',
        'scott.brownlee@johnsonelectric.com',
        'shivam.bhatt@johnsonelectric.com',
        'jamie.pearce@johnsonelectric.com',
        'harsh.thakar@johnsonelectric.com',
    ],
    'Backup_Supervisors': [
        'mark.morse@johnsonelectric.com'
    ],
    'Team_Leads': [
        'nathan.klein-geltink@johnsonelectric.com',
        'lisa.baker@johnsonelectric.com',
        'geoff.goldsack@johnsonelectric.com'
    ],
    'Quality': [
        'geoff.perrier@johnsonelectric.com'
    ],
    'Testing_group': [
        'chris.strutton@johnsonelectric.com',
        'tyler.careless@johnsonelectric.com',
    ]
}

# Function to combine email groups
def get_combined_email_groups(*group_names):
    email_list = []
    for group_name in group_names:
        email_list.extend(EMAIL_GROUPS.get(group_name, []))
    return email_list

# Task to send an individual email
@shared_task
def send_individual_email(recipient, code, barcode, scan_time):
    subject_with_code = f"Duplicate Barcode Alert - Unlock Code: {code}"
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

    msg = MIMEText(email_body, 'html')
    msg['Subject'] = subject_with_code
    msg['From'] = 'noreply@johnsonelectric.com'
    msg['To'] = recipient

    try:
        server = smtplib.SMTP('smtp01.stackpole.ca', 25)
        server.sendmail(msg['From'], [recipient], msg.as_string())
        server.quit()
        return {"message": f"Email sent successfully to {recipient}"}
    except Exception as e:
        return {"error": f"Error sending email to {recipient}: {str(e)}"}
