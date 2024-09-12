import os
import json
from django.http import JsonResponse
from django.template.loader import render_to_string
from .tasks import send_email_task
from django.views.decorators.csrf import csrf_exempt



# ========================================================
# ========================================================
# ============= Emailer API Endpoint Usage ===============
# ========================================================
# ========================================================


# API Endpoint: send_email_from_topic

# Description:
# ---------------
# This API endpoint allows other applications to send templated emails using a predefined "topic". Each email topic has 
# an associated email template, a list of recipients, and a set of dynamic variables that can be filled in when making a 
# request. Once the topic is set up with the necessary template, recipients, and variable keys, an application can trigger 
# an email by sending a POST request to the endpoint with the required data.

# Setup Process for a New Email Topic:
# ------------------------------------
# 1. **Create a directory for the new topic (Can honestly just copy and paste existing topics and just change the names and contents within files):**
#    - Inside the `templates/emailer/` directory, create a new folder named after the topic (e.g., `templates/emailer/production_update/`).
   
# 2. **Create a recipients.txt file:**
#    - Inside the topic folder (e.g., `production_update/`), create a file called `recipients.txt` and add the email addresses
#      of the recipients. Each recipient should be listed on a new line:
#      ```
#      example1@domain.com
#      example2@domain.com
#      ```

# 3. **Create a variables.json file:**
#    - In the same folder, create a `variables.json` file, which contains the keys for the dynamic
#      variables to be used in the email template. For example:
#      ```json
#      {
#        "customer_name": "",
#        "order_number": "",
#        "total_amount": ""
#      }
#      ```
#    - These keys can be filled dynamically when sending the request.

# 4. **Create the template.html file:**
#    - Create a `template.html` file in the same folder to define the structure of the email. 
#      Use the keys from the `variables.json` file to insert dynamic content. Example:
#      ```html
#      <!DOCTYPE html>
#      <html>
#      <body>
#          <p>Hello {{ customer_name }},</p>
#          <p>Your order with number {{ order_number }} has been successfully processed.</p>
#          <p>Total Amount: {{ total_amount }}</p>
#      </body>
#      </html>
#      ```


# Usage Example:
# ----------------
# Once an email topic is set up, other apps or services can send a POST request to trigger the email for that topic.

# - **Endpoint:** `/api/emailer/send/production_update/`
# - **Method:** `POST`
# - **Request Body (JSON):**
#   ```json
#   {
#     "subject": "Order Confirmation",
#     "variables": {
#       "customer_name": "John Doe",
#       "order_number": "123456",
#       "total_amount": "$99.99"
#     }
#   }


# Example View:
# ---------------

# import requests
# from django.http import JsonResponse
# from django.views.decorators.csrf import csrf_exempt
# from django.urls import reverse  # To construct relative URLs

# @csrf_exempt
# def send_order_confirmation_email(request):
#     if request.method == 'POST':
#         # Extract the necessary data from the request
#         customer_name = request.POST.get('customer_name')
#         order_number = request.POST.get('order_number')
#         total_amount = request.POST.get('total_amount')

#         if not customer_name or not order_number or not total_amount:
#             return JsonResponse({"error": "Missing required fields"}, status=400)

#         # Prepare the data to send to the emailer API
#         email_data = {
#             "subject": "Order Confirmation",
#             "variables": {
#                 "customer_name": customer_name,
#                 "order_number": order_number,
#                 "total_amount": total_amount
#             }
#         }

#         # Construct the relative URL for the emailer API
#         email_api_url = request.build_absolute_uri(reverse('send_email_from_topic', args=['order_confirmation']))
#         headers = {"Content-Type": "application/json"}

#         # Send a POST request to the emailer API
#         response = requests.post(email_api_url, headers=headers, json=email_data)

#         # Handle the response from the emailer API
#         if response.status_code == 200:
#             return JsonResponse({"status": "Email sent successfully"})
#         else:
#             return JsonResponse({"error": f"Failed to send email: {response.json()}"}, status=500)

#     else:
#         return JsonResponse({"error": "Invalid request method"}, status=405)




# Example Curl: 
# ----------------

# curl -X POST http://localhost:8081/api/emailer/send/order_confirmation/ \
# -H "Content-Type: application/json" \
# -d '{
#   "subject": "Order Confirmation",
#   "variables": {
#     "customer_name": "Alice Johnson",
#     "order_number": "789123",
#     "total_amount": "$150.00"
#   }
# }'



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
