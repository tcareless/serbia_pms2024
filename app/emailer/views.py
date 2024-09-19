import json
from django.http import JsonResponse
from django.template.loader import render_to_string
from .tasks import send_email_task
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings



@csrf_exempt
def send_email(request):
    if request.method == 'POST':
        try:
            # Parse the incoming request body
            request_data = json.loads(request.body)

            # Extract required fields
            recipients = request_data.get('recipients', [])
            subject = request_data.get('subject', 'No Subject')
            html_template = request_data.get('html_template', '')
            dynamic_vars = request_data.get('variables', {})
            from_email = request_data.get('from_email', None)

            # Validation
            if not recipients:
                return JsonResponse({"error": "Recipients list cannot be empty"}, status=400)
            if not html_template:
                return JsonResponse({"error": "HTML template is required"}, status=400)

            # Ensure the default sender is used if no sender is provided
            from_email = from_email or settings.DEFAULT_FROM_EMAIL

            # Render the HTML email content by injecting dynamic variables
            html_message = render_to_string(html_template, dynamic_vars)

            # Debug: Show the HTML message
            print(f"Rendered HTML message: {html_message}")

            # Create a separate task for each recipient to send the email
            for recipient in recipients:
                send_email_task.delay([recipient], subject, "", html_message, from_email)
                print(f"Email task created for: {recipient}")

            return JsonResponse({"status": "Email tasks are being sent"}, status=200)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON format"}, status=400)
        except Exception as e:
            print(f"Error: {str(e)}")  # Log the error
            return JsonResponse({"error": str(e)}, status=500)
    else:
        return JsonResponse({"error": "Only POST requests are allowed"}, status=405)








# =============================================================================
# =============================================================================
# ============================== Sample Usage =================================
# =============================================================================
# =============================================================================


# import requests
# from django.http import JsonResponse
# from django.template.loader import render_to_string
# from django.urls import reverse

# def send_order_confirmation_email(request):
#     if request.method == 'POST':
#         # Extract necessary data
#         customer_name = request.POST.get('customer_name')
#         order_number = request.POST.get('order_number')
#         total_amount = request.POST.get('total_amount')

#         if not customer_name or not order_number or not total_amount:
#             return JsonResponse({"error": "Missing required fields"}, status=400)

#         # Build the dynamic variables
#         variables = {
#             "customer_name": customer_name,
#             "order_number": order_number,
#             "total_amount": total_amount
#         }

#         # Define the HTML template path (relative to the 'orders' app templates directory)
#         html_template = 'orders/emails/order_confirmation.html'

#         # Define recipients
#         recipients = ['customer@example.com']

#         # Prepare data for the emailer API
#         email_data = {
#             "recipients": recipients,
#             "subject": "Your Order Confirmation",
#             "html_template": html_template,
#             "variables": variables,
#         }

#         # URL of the emailer service
#         emailer_url = request.build_absolute_uri(reverse('send_email'))
        
#         headers = {"Content-Type": "application/json"}

#         # Send a POST request to the emailer app
#         response = requests.post(emailer_url, headers=headers, json=email_data)

#         if response.status_code == 200:
#             return JsonResponse({"status": "Email sent successfully"})
#         else:
#             return JsonResponse({"error": "Failed to send email"}, status=500)






# Template in Another App: orders/templates/orders/emails/order_confirmation.html

# <!DOCTYPE html>
# <html>
# <body>
#     <p>Hello {{ customer_name }},</p>
#     <p>Your order with number {{ order_number }} has been successfully processed.</p>
#     <p>Total Amount: {{ total_amount }}</p>
# </body>
# </html>
