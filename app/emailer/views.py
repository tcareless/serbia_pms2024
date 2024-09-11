import json
from django.http import JsonResponse
from django.core.mail import send_mail
from django.conf import settings
from .tasks import send_email_task
from django.views.decorators.csrf import csrf_exempt


# =========================================================================
# ===================== Email API Endpoint Usage ==========================
# =========================================================================

# The `send_email` view handles POST requests to send emails asynchronously using Celery.
# Other apps can call this API by sending a JSON payload containing the recipients,
# subject, and HTML message content.

# Example request payload (JSON format):
# {
#   "to": ["recipient1@example.com", "recipient2@example.com"],
#   "subject": "Subject of the Email",
#   "html_message": "<h1>This is an HTML version of the email.</h1>"
# }

# Example cURL usage to call this API endpoint:
# curl -X POST http://127.0.0.1:8000/api/emailer/send/ \
# -H "Content-Type: application/json" \
# -d '{
#       "to": ["recipient1@example.com", "recipient2@example.com"],
#       "subject": "Test Email",
#       "html_message": "<h1>This is a test email sent from the API.</h1>"
#     }'



@csrf_exempt
def send_email(request):
    if request.method == 'POST':
        try:
            # Load JSON data from the request body
            data = json.loads(request.body)
            to_emails = data.get('to', [])
            subject = data.get('subject', '')
            html_message = data.get('html_message', '')

            if not to_emails or not subject:
                return JsonResponse({"error": "Missing required fields: 'to' or 'subject'"}, status=400)

            # Pass the email task to Celery for background sending
            send_email_task.delay(to_emails, subject, html_message)

            return JsonResponse({"status": "Email is being sent"}, status=200)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON format"}, status=400)
    else:
        return JsonResponse({"error": "Only POST requests are allowed"}, status=405)
