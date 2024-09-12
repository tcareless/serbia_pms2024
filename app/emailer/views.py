import os
import json
from django.http import JsonResponse
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

def load_variable_keys(email_topic):
    """Load variable keys from the variables.json file"""
    variables_file = os.path.join(get_email_topic_directory(email_topic), 'variables.json')
    print(f"Looking for variables file: {variables_file}")  # Debug statement
    if not os.path.exists(variables_file):
        print("Variables file not found!")  # Debug statement
        return {}
    with open(variables_file, 'r') as f:
        variable_keys = json.load(f)
    print(f"Loaded variable keys: {variable_keys}")  # Debug statement
    return variable_keys

@csrf_exempt
def send_email_from_topic(request, email_topic):
    if request.method == 'POST':
        try:
            # Debug: Print the raw body to see what's coming in
            print(f"Raw request body: {request.body}")
            
            # Try loading the request body as JSON
            try:
                request_data = json.loads(request.body)
            except json.JSONDecodeError as e:
                print(f"Error parsing JSON: {e}")
                return JsonResponse({"error": "Invalid JSON format"}, status=400)

            # Debug: Print the loaded JSON data
            print(f"Parsed JSON data: {request_data}")
            
            # Proceed with the rest of your logic
            recipients = load_recipients(email_topic)
            if not recipients:
                print("No recipients found!")  # Debug statement
                return JsonResponse({"error": "No recipients found"}, status=400)
            
            variable_keys = load_variable_keys(email_topic)
            template_file = os.path.join(get_email_topic_directory(email_topic), 'template.html')

            if not os.path.exists(template_file):
                print("Template file not found!")  # Debug statement
                return JsonResponse({"error": "Template not found"}, status=404)

            # Get subject and dynamic variables from the request
            subject = request_data.get('subject', 'No Subject')
            dynamic_vars = request_data.get('variables', {})

            # Merge dynamic values into the variable keys from variables.json
            variables = {key: dynamic_vars.get(key, '') for key in variable_keys}
            print(f"Merged variables: {variables}")  # Debug statement

            # Render the email HTML using the merged variables
            html_message = render_to_string(template_file, variables)
            print(f"Rendered HTML message: {html_message}")  # Debug statement

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
