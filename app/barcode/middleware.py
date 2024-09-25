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

class BatchScanLockoutMiddleware:
    """
    Middleware to handle the lockout for batch scans when invalid barcodes are detected.
    This middleware checks if the user has been locked out during the batch scan process
    and redirects them to the batch lockout page if necessary.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Check if the session indicates the batch scan lockout
        batch_locked = request.session.get('batch_locked', False)
        batch_unlock_code_submitted = request.session.get('batch_unlock_code_submitted', False)

        # If batch is locked and unlock code is not yet submitted, redirect to lockout page
        if batch_locked and not batch_unlock_code_submitted:
            # Prevent an infinite loop by ensuring the user is not already on the lockout page
            if request.path != reverse('barcode:batch-lockout'):
                return redirect('barcode:batch-lockout')

        return self.get_response(request)
