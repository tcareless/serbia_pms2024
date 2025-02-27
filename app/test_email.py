import smtplib
from email.message import EmailMessage
import time
import socket

def send_test_email():
    # Start timing
    start_time = time.time()

    # Email server settings
    smtp_host = 'smtp01.stackpole.ca'
    smtp_port = 25

    # Email details
    subject = "Test Email"
    body = "This is a test email to check the sending time."
    from_email = 'noreply@johnsonelectric.com'
    recipient_list = [
        'tyler.careless@johnsonelectric.com',
        'tyler.careless@johnsonelectric.com',
        'tyler.careless@johnsonelectric.com',
        'tyler.careless@johnsonelectric.com',
        'tyler.careless@johnsonelectric.com',
        'tyler.careless@johnsonelectric.com',
        'tyler.careless@johnsonelectric.com',
        'tyler.careless@johnsonelectric.com',
        'tyler.careless@johnsonelectric.com',
        'tyler.careless@johnsonelectric.com',
        'tyler.careless@johnsonelectric.com',
        'tyler.careless@johnsonelectric.com',
        'tyler.careless@johnsonelectric.com',
        'tyler.careless@johnsonelectric.com',
        'tyler.careless@johnsonelectric.com',
        'tyler.careless@johnsonelectric.com',
        'tyler.careless@johnsonelectric.com',
        'tyler.careless@johnsonelectric.com',
        'tyler.careless@johnsonelectric.com',
        'tyler.careless@johnsonelectric.com',
        'tyler.careless@johnsonelectric.com',
        'tyler.careless@johnsonelectric.com',
        'tyler.careless@johnsonelectric.com',
        'tyler.careless@johnsonelectric.com',
        'tyler.careless@johnsonelectric.com',
        'tyler.careless@johnsonelectric.com',
        'tyler.careless@johnsonelectric.com',
        'tyler.careless@johnsonelectric.com',
        'tyler.careless@johnsonelectric.com',
        'tyler.careless@johnsonelectric.com',
        'tyler.careless@johnsonelectric.com',
        'tyler.careless@johnsonelectric.com',
        'tyler.careless@johnsonelectric.com',
        'tyler.careless@johnsonelectric.com',
        'tyler.careless@johnsonelectric.com',
        'tyler.careless@johnsonelectric.com',
        'tyler.careless@johnsonelectric.com',
        'tyler.careless@johnsonelectric.com',
        'tyler.careless@johnsonelectric.com',
        'tyler.careless@johnsonelectric.com',
    ]

    # Create the email message
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = from_email
    msg['To'] = 'tyler.careless@johnsonelectric.com'
    msg['Bcc'] = ', '.join(recipient_list)
    msg.set_content(body)

    try:
        # Connect to the SMTP server
        server = smtplib.SMTP(smtp_host, smtp_port)
        server.set_debuglevel(1)
        server.ehlo()

        # Send email but DO NOT wait for server response
        server.sendmail(from_email, recipient_list, msg.as_string())
        
        # Force-close the connection immediately
        server.sock.close()
        print("Email sent (connection force-closed)!")

    except Exception as e:
        print(f"Failed to send email: {e}")

    # End timing
    end_time = time.time()
    duration = end_time - start_time

    print(f"Email sent to {len(recipient_list)} recipients in {duration:.2f} seconds")

if __name__ == "__main__":
    send_test_email()
