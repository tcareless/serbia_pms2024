import os
import json
from django.http import JsonResponse
from django.core.mail import send_mail
from django.template.loader import render_to_string
from .tasks import send_email_task
from django.views.decorators.csrf import csrf_exempt

# Use the current directory relative to the emailer app
EMAIL_TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), 'templates/emailer')

def get_email_topic_directory(email_topic):
    email_topic_dir = os.path.join(EMAIL_TEMPLATE_DIR, email_topic)
    print(f"Looking for email topic directory: {email_topic_dir}")  # Debug statement
    return email_topic_dir

def load_recipients(email_topic):
    recipients_file = os.path.join(get_email_topic_directory(email_topic), 'recipients.txt')
    print(f"Looking for recipients file: {recipients_file}")  # Debug statement
    if not os.path.exists(recipients_file):
        print("Recipients file not found!")  # Debug statement
        return []
    with open(recipients_file, 'r') as f:
        recipients = [line.strip() for line in f.readlines() if line.strip()]
    print(f"Loaded recipients: {recipients}")  # Debug statement
    return recipients

def load_variables(email_topic):
    variables_file = os.path.join(get_email_topic_directory(email_topic), 'variables.json')
    print(f"Looking for variables file: {variables_file}")  # Debug statement
    if not os.path.exists(variables_file):
        print("Variables file not found!")  # Debug statement
        return {}
    with open(variables_file, 'r') as f:
        variables = json.load(f)
    print(f"Loaded variables: {variables}")  # Debug statement
    return variables

@csrf_exempt
def send_email_from_topic(request, email_topic):
    if request.method == 'POST':
        try:
            # Load the recipients, variables, and template for the email topic
            recipients = load_recipients(email_topic)
            if not recipients:
                print("No recipients found!")  # Debug statement
                return JsonResponse({"error": "No recipients found"}, status=400)
            
            variables = load_variables(email_topic)
            template_file = os.path.join(get_email_topic_directory(email_topic), 'template.html')
            print(f"Looking for template file: {template_file}")  # Debug statement

            if not os.path.exists(template_file):
                print("Template file not found!")  # Debug statement
                return JsonResponse({"error": "Template not found"}, status=404)

            # Render the email HTML using the variables
            html_message = render_to_string(template_file, variables)
            print(f"Rendered HTML message: {html_message}")  # Debug statement
            
            # Optional: Accept overriding variables via request body
            request_data = json.loads(request.body)
            subject = request_data.get('subject', 'No Subject')
            dynamic_vars = request_data.get('variables', {})
            html_message = html_message.format(**dynamic_vars)

            print(f"Final HTML message: {html_message}")  # Debug statement

            # Pass the email task to Celery for background sending
            send_email_task.delay(recipients, subject, "", html_message)
            print(f"Email sent to: {recipients}")  # Debug statement

            return JsonResponse({"status": "Email is being sent"}, status=200)
        except Exception as e:
            print(f"Error occurred: {str(e)}")  # Debug statement
            return JsonResponse({"error": str(e)}, status=400)
    else:
        print("Invalid request method!")  # Debug statement
        return JsonResponse({"error": "Only POST requests are allowed"}, status=405)
