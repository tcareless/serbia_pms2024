import smtplib
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

def send_email(subject, html_content, text_content, recipients):
    # Start timing
    start_time = time.time()

    # Create a multipart/alternative MIME message
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = "noreply@johnsonelectric.com"
    msg["To"] = "noreply@johnsonelectric.com"  # Display only; actual recipients go in sendmail

    # Create the plain text and HTML parts
    part1 = MIMEText(text_content, "plain")
    part2 = MIMEText(html_content, "html")

    # Attach parts in order (the email client picks the best version to display)
    msg.attach(part1)
    msg.attach(part2)

    # Send the email via SMTP
    with smtplib.SMTP("smtp01.stackpole.ca", 25) as server:
        server.sendmail(msg["From"], recipients, msg.as_string())

    # End timing
    end_time = time.time()
    duration = end_time - start_time
    print(f"Email sent to {len(recipients)} recipients in {duration:.2f} seconds")






if __name__ == "__main__":
    recipients = ["tyler.careless@johnsonelectric.com",
                  "tyler.careless@johnsonelectric.com",
                  ]
    subject = "HTML Template Email Test"
    html_content = """<html>
  <body>
    <h1>Hello Tyler!</h1>
    <p>This is an <strong>HTML test email</strong> to check the sending time.</p>
    <p>This is a dynamically filled message!</p>
    <p>Best regards,<br>Your IT Team</p>
  </body>
</html>"""
    text_content = "This is a test email to check the sending time."

    send_email(subject, html_content, text_content, recipients)
