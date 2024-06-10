import smtplib
import random
from email.mime.text import MIMEText

EMAIL_SERVER = 'smtp01.stackpole.ca'
EMAIL_FROM = 'tyler.careless@johnsonelectric.com'
EMAIL_SUBJECT = 'Subject of email'
EMAIL_LIST = ['tyler.careless@johnsonelectric.com']

def generate_unlock_code():
    return '{:03d}'.format(random.randint(0, 999))

def send_unlock_code_email(code):
    msg = MIMEText(f'The new unlock code is: {code}')
    msg['Subject'] = EMAIL_SUBJECT
    msg['From'] = EMAIL_FROM
    msg['To'] = ', '.join(EMAIL_LIST)

    with smtplib.SMTP(EMAIL_SERVER) as server:
        server.sendmail(EMAIL_FROM, EMAIL_LIST, msg.as_string())

def generate_and_send_code():
    code = generate_unlock_code()
    send_unlock_code_email(code)
    return code
