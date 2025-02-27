import smtplib
from email.message import EmailMessage
import time

def send_test_email():
    # Start timing
    start_time = time.time()

    # Email server settings
    smtp_host = 'smtp01.stackpole.ca'
    smtp_port = 25
    smtp_username = None  # Add username if required
    smtp_password = None  # Add password if required

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

    ]

    # Create the email message
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = from_email
    msg['To'] = 'tyler.careless@johnsonelectric.com'  # Main recipient for display
    msg['Bcc'] = ', '.join(recipient_list)  # Send as BCC
    msg.set_content(body)

    try:
        # Connect to the SMTP server
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.set_debuglevel(1)  # Show communication with the server
            server.ehlo()

            # Send the email
            server.send_message(msg)
            print("Email sent successfully!")
    except Exception as e:
        print(f"Failed to send email: {e}")

    # End timing
    end_time = time.time()
    duration = end_time - start_time

    print(f"Email sent to {len(recipient_list)} recipients in {duration:.2f} seconds")

if __name__ == "__main__":
    send_test_email()
