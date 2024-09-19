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
            html_content = request_data.get('html_content', '')  # Use pre-rendered HTML content
            from_email = request_data.get('from_email', None)

            # Validation
            if not recipients:
                return JsonResponse({"error": "Recipients list cannot be empty"}, status=400)
            if not html_content:
                return JsonResponse({"error": "HTML content is required"}, status=400)

            # Ensure the default sender is used if no sender is provided
            from_email = from_email or settings.DEFAULT_FROM_EMAIL

            # Debug: Show the HTML message
            print(f"Received HTML content: {html_content}")

            # Create a separate task for each recipient to send the email
            for recipient in recipients:
                send_email_task.delay([recipient], subject, "", html_content, from_email)
                print(f"Email task created for: {recipient}")

            return JsonResponse({"status": "Email tasks are being sent"}, status=200)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON format"}, status=400)
        except Exception as e:
            print(f"Error: {str(e)}")  # Log the error
            return JsonResponse({"error": str(e)}, status=500)
    else:
        return JsonResponse({"error": "Only POST requests are allowed"}, status=405)




# ==============================================================================================
# ==============================================================================================
# ======================== Duplicate Email Example View ========================================
# ==============================================================================================
# ==============================================================================================

# This just shows what a view may look like inside a different app to get
# these emails to send with celery using the emailer app

# from django.template.loader import render_to_string
# import requests
# from django.urls import reverse
# from django.http import JsonResponse

# def send_email_to_emailer(request, code, barcode, scan_time, part_number):
#     """
#     Sends a POST request to the emailer app to send an email notification.
#     """
#     # Render the HTML content in the 'barcode' app itself
#     html_content = render_to_string('barcode/duplicate_email.html', {
#         'code': code,
#         'barcode': barcode,
#         'scan_time': scan_time,
#         'part_number': part_number
#     })

#     # Prepare the data to send to the 'emailer' app
#     email_data = {
#         "recipients": ["tyler.careless@johnsonelectric.com"],
#         "subject": "Duplicate Barcode Scanned",
#         "html_content": html_content  # Send the fully rendered HTML content
#     }

#     # Construct the URL for the emailer service
#     emailer_url = request.build_absolute_uri(reverse('send_email'))

#     headers = {"Content-Type": "application/json"}

#     try:
#         # Send a POST request to your emailer app
#         response = requests.post(emailer_url, headers=headers, json=email_data)
#         response.raise_for_status()  # Raise an error for bad status codes

#         return response.json()
#     except requests.exceptions.RequestException as e:
#         print(f"Error sending email: {e}")
#         return {"error": str(e)}

