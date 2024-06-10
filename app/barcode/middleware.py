from django.shortcuts import redirect
from django.urls import reverse

class CheckUnlockCodeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Allow access to static files and admin for easier development
        if request.path.startswith('/static/') or request.path.startswith('/admin/'):
            return self.get_response(request)

        if request.session.get('unlock_code_provided', False):
            return self.get_response(request)

        if request.path != reverse('barcode:duplicate-found') and not request.path.endswith('/verify_unlock_code'):
            return redirect('barcode:duplicate-found')

        response = self.get_response(request)
        return response
