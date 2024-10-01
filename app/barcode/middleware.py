from django.shortcuts import redirect
from django.urls import reverse

class CheckUnlockCodeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        duplicate_found = request.session.get('duplicate_found', False)
        unlock_code_submitted = request.session.get('unlock_code_submitted', False)
        unlock_code = request.session.get('unlock_code')

        # print(f"duplicate_found: {duplicate_found}")
        # print(f"unlock_code_submitted: {unlock_code_submitted}")
        # print(f"unlock_code: {unlock_code}")

        if not duplicate_found or unlock_code_submitted:
            return self.get_response(request)

        if request.path != reverse('barcode:duplicate-found') and not request.path.endswith('/verify_unlock_code'):
            return redirect('barcode:duplicate-found')

        return self.get_response(request)


from django.shortcuts import redirect
from django.urls import reverse

class SupervisorLockoutMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Check if the user is in a "lockout" state
        if request.path[:9] == '/barcode/':
            lockout_active = request.session.get('lockout_active', False)
            unlock_code_submitted = request.session.get('unlock_code_submitted', False)

            # If the user is locked out and hasn't submitted the unlock code
            if lockout_active and not unlock_code_submitted:
                # If the request is not for the lockout page itself, redirect to lockout page
                if request.path != reverse('barcode:lockout_page'):
                    return redirect('barcode:lockout_page')

        # If the unlock code has been submitted, allow the request to proceed
        return self.get_response(request)
