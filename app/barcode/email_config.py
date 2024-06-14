import random
import requests
from datetime import datetime

EMAIL_SUBJECT_TEMPLATE = 'Duplicate Scanned at AB1V/10R140 Unlock Code:{code}'

def generate_unlock_code():
    """
    Generates a random 3-digit unlock code.
    """
    return '{:03d}'.format(random.randint(0, 999))

def send_unlock_code_email_to_flask(code, barcode, scan_time):
    """
    Sends the unlock code, barcode, and scan time to the Flask app for email dispatch.
    """
    url = 'http://localhost:5001/send-email'
    
    # Format scan_time to a nice string
    formatted_scan_time = scan_time.strftime('%Y-%m-%d %H:%M:%S')
    
    payload = {
        'code': code,
        'barcode': barcode,
        'scan_time': formatted_scan_time  # Use the formatted scan time string
    }
    headers = {'Content-Type': 'application/json'}
    response = requests.post(url, json=payload, headers=headers)
    return response.json()

def generate_and_send_code(barcode, scan_time):
    """
    Generates an unlock code and sends it to the Flask app for email dispatch.
    """
    code = generate_unlock_code()
    # Ensure scan_time is a datetime object
    if isinstance(scan_time, str):
        scan_time = datetime.fromisoformat(scan_time)
    response = send_unlock_code_email_to_flask(code, barcode, scan_time)
    if 'error' in response:
        print(f"Error sending email: {response['error']}")
    else:
        print("Email sent successfully.")
    return code
