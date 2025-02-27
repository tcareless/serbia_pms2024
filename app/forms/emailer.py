import socket
import time

def send_hybrid_email(recipient_list):
    """
    Sends an email to a list of recipients using a fast, minimal confirmation SMTP method.
    
    Args:
        recipient_list (list): List of email addresses to send the email to.
    """
    # Start timing
    start_time = time.time()

    # Email server settings
    smtp_host = 'smtp01.stackpole.ca'
    smtp_port = 25

    # Email details
    from_email = 'noreply@johnsonelectric.com'
    to_email = from_email  # Display only (To: field), actual recipients are in BCC

    # Construct raw SMTP message
    message = f"""\ 
From: {from_email}
To: {to_email}
Subject: Test Email
MIME-Version: 1.0
Content-Type: text/plain; charset="utf-8"
Content-Transfer-Encoding: 7bit

This is a test email to check the sending time.
.
"""

    # Connect to SMTP server
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((smtp_host, smtp_port))

        # Get initial response
        s.recv(1024)

        # Send EHLO and confirm ready
        s.sendall(b"EHLO fast-client\r\n")
        s.recv(1024)  # Wait for 250 OK

        # Send MAIL FROM
        s.sendall(f"MAIL FROM:<{from_email}>\r\n".encode())
        s.recv(1024)  # Wait for 250 OK

        # Send RCPT TO for all recipients
        for recipient in recipient_list:
            s.sendall(f"RCPT TO:<{recipient}>\r\n".encode())
            s.recv(1024)  # Wait for 250 OK

        # Start DATA section and wait for confirmation
        s.sendall(b"DATA\r\n")
        response = s.recv(1024)
        if b"354" not in response:
            print("Server did not accept DATA command.")
            return
        
        # Send message body and end with single period
        s.sendall(message.encode())

        # Immediately close socket after sending data (minimal confirmation)
        s.close()

    print("Email sent (connection force-closed after DATA)!")

    # End timing
    end_time = time.time()
    duration = end_time - start_time

    print(f"Email sent to {len(recipient_list)} recipients in {duration:.2f} seconds")

if __name__ == "__main__":
    # Example usage with custom recipient list
    recipients = [
        'tyler.careless@johnsonelectric.com',
        'tyler.careless@johnsonelectric.com',
        'tyler.careless@johnsonelectric.com',
        'tyler.careless@johnsonelectric.com',
        'tyler.careless@johnsonelectric.com',
        'tyler.careless@johnsonelectric.com',
        'tyler.careless@johnsonelectric.com',
        'tyler.careless@johnsonelectric.com',
        'tyler.careless@johnsonelectric.com',
        'tyler.careless@johnsonelectric.com'
    ]
    send_hybrid_email(recipients)
