import random
import requests

EMAIL_SUBJECT_TEMPLATE = 'Duplicate Scanned at AB1V/10R140 Unlock Code:{code}'

def generate_unlock_code():
    return '{:03d}'.format(random.randint(0, 999))

def send_unlock_code_email_to_flask(code, barcode, scan_time):
    url = 'http://localhost:5000/send-email'
    payload = {
        'code': code,
        'barcode': barcode,
        'scan_time': scan_time
    }
    headers = {'Content-Type': 'application/json'}
    response = requests.post(url, json=payload, headers=headers)
    return response.json()

def generate_and_send_code(barcode, scan_time):
    code = generate_unlock_code()
    response = send_unlock_code_email_to_flask(code, barcode, scan_time)
    if 'error' in response:
        print(f"Error sending email: {response['error']}")
    else:
        print("Email sent successfully.")
    return code
