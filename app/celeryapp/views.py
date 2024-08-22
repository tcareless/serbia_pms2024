from django.shortcuts import render
from django.http import JsonResponse
from .tasks import send_email_task

# Dummy email list + your email for verification
DUMMY_EMAILS = ['tyler.careless@johnsonelectric.com'] * 20


def send_emails_view(request):
    if request.method == 'POST':
        subject = request.POST.get('subject', 'Test Email')
        message = request.POST.get('message', 'This is a test email.')

        # Queue a task for each recipient in the list
        for email in DUMMY_EMAILS:
            send_email_task.apply_async(args=[subject, message, email])

        return JsonResponse({'status': 'Emails are being sent in the background.'})

    return render(request, 'celeryapp/send_emails.html')

def counter_view(request):
    count = int(request.GET.get('count', 0))
    return JsonResponse({'count': count})