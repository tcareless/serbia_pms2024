from loguru import logger as loguru_logger
import re
from django.utils import timezone
from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import BarcodeScanForm, BatchBarcodeScanForm, UnlockCodeForm
from barcode.models import LaserMark, LaserMarkDuplicateScan, BarCodePUN
import time
from .email_config import generate_and_send_code
import random
import logging
import datetime
import json
from django.urls import reverse
import humanize
from django.utils.timezone import localtime, make_aware, is_naive
import requests
from .models import DuplicateBarcodeEvent
from django.utils.dateparse import parse_datetime
from django.utils.timezone import now as timezone_now
import loguru
from datetime import timedelta, datetime
from django.http import JsonResponse
from .models import LaserMark, LaserMarkDuplicateScan
import MySQLdb







# Configure loguru to log to a file
loguru_logger.remove()  # Remove any existing handlers
loguru_logger.add("app/logs/duplicate_barcode_logs/duplicate_barcodes.log", level="INFO")

# Standard logging for other views
logger = logging.getLogger(__name__)


def sub_index(request):
    return redirect('barcode:barcode_index') 


def barcode_index_view(request):
    context = {}
    context["main_heading"] = "Barcode Index"
    context["title"] = "Barcode Index - pmsdata12"
    return render(request, f'barcode/index_barcode.html', context)


"""
Duplicate Scanning:
This code provides a check that barcodes are valid for the current part number and that the barcode has not been 
scanned previously.  
Parts are scanned as they are packed.  The scan is automatically submitted by pressing enter.  The scanner 
automatically adds Enter to the end of the scanned barcode.  
The scan is verified to contain the correct data for the part type and that all variable sections contain sane data.  
If any of the data is no good, an error screen is displayed to the operator.  
The the time and date of each scan is saved in the database.  If the same barcode is scanned a second time an error 
screen is displayed to the operator.  
If the barcode is valid, the screen refreshes so the operator can enter the next code.  A running count is 
maintained.  The running count resets automatically if the operator changes the part type and scans the next part. 
The running count can be set to any value using the Set Counter button.  Pressing the Set Counter button without
entering a new value sets the counter to zero.  

# - TODO: *SIGNAL* Create duplicate scan signal so it can be reacted to possible email notification etc
"""

# Does not return processed barcode

def verify_barcode(part_id, barcode):

    current_part_PUN = BarCodePUN.objects.get(id=part_id)
    barcode_result = {
        'barcode': barcode,
        'part_number': current_part_PUN.part_number,
        'PUN': current_part_PUN.regex,
        'grade': '',
        'status': '',
    }

    # check against the PUN
    if not re.search(current_part_PUN.regex, barcode):
        barcode_result['status'] = 'malformed'

    # set lm to None to prevent error
    lm = None
    # does barcode exist?
    lm, created = LaserMark.objects.get_or_create(bar_code=barcode)
    if created:
        # laser mark does not exist in db.  Need to create it.
        lm.part_number = current_part_PUN.part_number
        lm.save()
        barcode_result['status'] = 'created'

    # verify the barcode has a passing grade on file?
    if lm.grade not in ('A', 'B', 'C'):
        barcode_result['status'] = 'failed_grade'

    # has barcode been duplicate scanned?
    dup_scan, created = LaserMarkDuplicateScan.objects.get_or_create(
        laser_mark=lm)
    if not created:
        barcode_result['scanned_at'] = dup_scan.scanned_at
        barcode_result['status'] = 'duplicate'

    else:
        # barcode has not been scanned previously
        dup_scan.save()

    barcode_result['grade'] = lm.grade

    print(f'{current_part_PUN.part_number}:{barcode}')
    return barcode_result


def send_email_to_flask(code, barcode, scan_time):

    # url = 'http://localhost:5002/send-email' 
    url = 'http://10.4.1.234:5001/send-email' 
    
    payload = {
        'code': code,
        'barcode': barcode,
        'scan_time': scan_time  # Already formatted string
    }
    headers = {'Content-Type': 'application/json'}
    
    try:
        # Set a very short timeout to not wait for a response
        requests.post(url, json=payload, headers=headers, timeout=0.001)
    except requests.exceptions.RequestException as e:
        # This will catch the timeout error
        print(f"Request sent to Flask: {e}")

    # Return immediately
    return JsonResponse({'status': 'Email task sent to Flask service'})

def generate_unlock_code():
    """
    Generates a random 3-digit unlock code.
    """
    return '{:03d}'.format(random.randint(0, 999))

def generate_and_send_code(barcode, scan_time, part_number):
    code = generate_unlock_code()
    
    # Convert scan_time to datetime object if it's in string format
    if isinstance(scan_time, str):
        scan_time = datetime.strptime(scan_time, '%Y-%m-%dT%H:%M:%S.%f%z')
    
    # Subtract 4 hours from the scan time
    adjusted_scan_time = scan_time - timedelta(hours=4)
    
    # Format the scan time to the desired string format
    formatted_scan_time = adjusted_scan_time.strftime('%Y-%m-%d %H:%M:%S')
    
    response = send_email_to_flask(code, barcode, formatted_scan_time)
    if 'error' in response:
        print(f"Error sending email: {response['error']}")

    
    # Subtract 4 hours from the current time for event_time if needed
    event_time = timezone_now() - timedelta(hours=4)


    # Log the event to the database
    DuplicateBarcodeEvent.objects.create(
        barcode=barcode,
        part_number=part_number,
        scan_time=adjusted_scan_time,
        unlock_code=code,
        event_time=event_time
    )
    
    return code

def duplicate_scan(request):
    context = {}
    tic = time.time()
    running_count = int(request.session.get('RunningCount', '0'))
    last_part_id = request.session.get('LastPartID', '0')
    current_part_id = last_part_id
    select_part_options = BarCodePUN.objects.filter(active=True).order_by('name').values()

    if request.method == 'GET':
        form = BarcodeScanForm()

    if request.method == 'POST':
        if 'switch-mode' in request.POST:
            context['active_part'] = current_part_id
            return redirect('barcode:duplicate-scan-check')

        if 'set_count' in request.POST:
            messages.add_message(request, messages.INFO, 'Count reset.')
            running_count = request.POST.get('count', 0) or 0
            running_count = int(running_count)
            form = BarcodeScanForm()

        elif 'btnsubmit' in request.POST:
            form = BarcodeScanForm(request.POST)

            if form.is_valid():
                barcode = form.cleaned_data.get('barcode')
                current_part_id = int(request.POST.get('part_select', '0'))
                current_part_PUN = BarCodePUN.objects.get(id=current_part_id)

                if not re.search(current_part_PUN.regex, barcode):
                    context['scanned_barcode'] = barcode
                    context['part_number'] = current_part_PUN.part_number
                    context['expected_format'] = current_part_PUN.regex
                    return render(request, 'barcode/malformed.html', context=context)

                lm, created = LaserMark.objects.get_or_create(bar_code=barcode)
                if created:
                    lm.part_number = current_part_PUN.part_number
                    lm.save()

                if lm.grade not in ('A', 'B', 'C'):
                    context['scanned_barcode'] = barcode
                    context['part_number'] = lm.part_number
                    context['grade'] = lm.grade
                    return render(request, 'barcode/failed_grade.html', context=context)

                dup_scan, created = LaserMarkDuplicateScan.objects.get_or_create(laser_mark=lm)
                if not created:
                    scan_time = dup_scan.scanned_at  # Use the original scan time
                    unlock_code = generate_and_send_code(barcode, scan_time, lm.part_number)
                    request.session['unlock_code'] = unlock_code
                    request.session['duplicate_found'] = True
                    request.session['unlock_code_submitted'] = False
                    request.session['duplicate_barcode'] = barcode
                    request.session['duplicate_part_number'] = lm.part_number
                    request.session['duplicate_scan_at'] = scan_time.strftime('%Y-%m-%d %H:%M:%S')

                    loguru.logger.info(f"Duplicate found: True, Barcode: {barcode}, Part Number: {lm.part_number}, Time of original scan: {scan_time}")


                    return redirect('barcode:duplicate-found')
                else:
                    dup_scan.save()
                    messages.add_message(request, messages.SUCCESS, 'Valid Barcode Scanned')
                    running_count += 1
                    request.session['LastPartID'] = current_part_id
                    form = BarcodeScanForm()
        else:
            current_part_id = int(request.POST.get('part_select', '0'))
            running_count = 0
            form = BarcodeScanForm()

    toc = time.time()
    request.session['RunningCount'] = running_count
    context['form'] = form
    context['running_count'] = running_count
    context['title'] = 'Duplicate Scan'
    context['scan_check'] = False
    context['active_part'] = current_part_id
    context['part_select_options'] = select_part_options
    context['timer'] = f'{toc-tic:.3f}'

    return render(request, 'barcode/dup_scan.html', context=context)


def duplicate_found_view(request):
    if request.method == 'POST':
        form = UnlockCodeForm(request.POST)

        if form.is_valid():
            submitted_code = form.cleaned_data['unlock_code']
            employee_id = form.cleaned_data['employee_id']
            reason = form.cleaned_data['reason']
            other_reason = form.cleaned_data['other_reason']
            user_reason = other_reason if reason == 'other' else dict(form.REASON_CHOICES).get(reason)

            if submitted_code == request.session.get('unlock_code'):
                request.session['unlock_code_submitted'] = True
                request.session['duplicate_found'] = False

                # Convert the scan_time back to a datetime object
                scan_time_str = request.session.get('duplicate_scan_at')
                scan_time = datetime.strptime(scan_time_str, '%Y-%m-%d %H:%M:%S')

                # Adjust the scan_time by subtracting 4 hours
                scan_time = scan_time - timedelta(hours=4)

                if scan_time:
                    # Log the event to the database with employee ID and user reason
                    event = DuplicateBarcodeEvent.objects.filter(
                        barcode=request.session['duplicate_barcode'],
                        unlock_code=request.session['unlock_code']
                    ).first()
                    event.employee_id = employee_id
                    event.user_reason = user_reason
                    event.save()

                    return redirect('barcode:duplicate-scan')
                else:
                    messages.error(request, 'Invalid scan time format. Please try again.')

    else:
        form = UnlockCodeForm()

    # Convert the scan_time back to a datetime object and adjust it
    scan_time_str = request.session.get('duplicate_scan_at', '')
    adjusted_scan_time_str = (datetime.strptime(scan_time_str, '%Y-%m-%d %H:%M:%S') - timedelta(hours=4)).strftime('%Y-%m-%d %H:%M:%S') if scan_time_str else ''

    context = {
        'scanned_barcode': request.session.get('duplicate_barcode', ''),
        'part_number': request.session.get('duplicate_part_number', ''),
        'duplicate_scan_at': adjusted_scan_time_str,
        'unlock_code': request.session.get('unlock_code'),
        'form': form,
    }

    return render(request, 'barcode/dup_found.html', context=context)

def send_new_unlock_code(request):
    barcode = request.session.get('duplicate_barcode', '')
    scan_time = request.session.get('duplicate_scan_at', '')
    part_number = request.session.get('duplicate_part_number', '')
    unlock_code = generate_and_send_code(barcode, scan_time, part_number)
    request.session['unlock_code'] = unlock_code
    request.session['duplicate_found'] = True
    request.session['unlock_code_submitted'] = False

    humanized_time = humanize.naturaltime(localtime(timezone_now()))

    loguru.logger.info(f"New unlock code generated: {unlock_code}")

    return redirect('barcode:duplicate-found')

def duplicate_scan_batch(request):
    context = {}
    tic = time.time()
    # get data from session
    last_part_id = request.session.get('LastPartID', '0')
    current_part_id = last_part_id

    select_part_options = BarCodePUN.objects.filter(
        active=True).order_by('name').values()
    if current_part_id == '0':
        if select_part_options.first():
            current_part_id = select_part_options.first()['id']
    current_part_PUN = BarCodePUN.objects.get(id=current_part_id)

    if request.method == 'GET':
        # clear the form
        form = BatchBarcodeScanForm()

    if request.method == 'POST':
        barcodes = request.POST.get('barcodes')
        if len(barcodes):
            form = BatchBarcodeScanForm(request.POST)

            if form.is_valid():
                barcodes = form.cleaned_data.get('barcodes').split("\r\n")

                posted_part_id = int(request.POST.get('part_select', '0'))
                if posted_part_id:
                    current_part_id = posted_part_id
                processed_barcodes = []
                for barcode in barcodes:

                    # get or create a laser-mark for the scanned code
                    processed_barcodes.append(
                        verify_barcode(current_part_id, barcode))
                    print(f'{current_part_PUN.part_number}:{barcode}')
                    

                for barcode in processed_barcodes:

                    # # Malformed Barcode
                    # if barcode['status'] == 'malformed':
                    #     print('Malformed Barcode')
                    #     context['scanned_barcode'] = barcode
                    #     context['part_number'] = current_part_PUN.part_number
                    #     context['expected_format'] = current_part_PUN.regex
                    #     return render(request, 'barcode/malformed.html', context=context)

                    # verify the barcode has a passing grade on file?
                    # if barcode['status'] == 'failed_grade':
                    #     context['scanned_barcode'] = barcode
                    #     context['part_number'] = current_part_PUN.part_number
                    #     context['grade'] = barcode['grade']
                    #     return render(request, 'barcode/failed_grade.html', context=context)

                    # barcode has already been scanned
                    # if barcode['status'] == 'duplicate':
                    #     context['scanned_barcode'] = barcode['barcode']
                    #     context['part_number'] = barcode['part_number']
                    #     context['duplicate_scan_at'] = barcode['scanned_at']
                    #     return render(request, 'barcode/dup_found.html', context=context)
                    pass

        else:
            current_part_id = int(request.POST.get('part_select', '0'))
            if current_part_id == '0':
                if select_part_options.first():
                    current_part_id = select_part_options.first()['id']
            form = BatchBarcodeScanForm()

    context['form'] = form
    context['title'] = 'Batch Duplicate Scan'
    context['active_part'] = current_part_id
    context['part_select_options'] = select_part_options
    current_part_PUN = BarCodePUN.objects.get(id=current_part_id)
    context['active_part_prefix'] = current_part_PUN.regex[1:5]

    regex = current_part_PUN.regex
    while (regex.find('(?P') != -1):
        start = regex.find('(?P')
        end = regex.index('>',start)
        regex = regex[:start+1] + regex[end+1:]
    context['active_PUN'] = regex
    
    context['parts_per_tray'] = current_part_PUN.parts_per_tray

    request.session['LastPartID'] = current_part_id

    toc = time.time()
    context['timer'] = f'{toc-tic:.3f}'

    return render(request, 'barcode/dup_scan_batch.html', context=context)

def duplicate_scan_check(request):
    context = {}
    tic = time.time()

    current_part_id = request.session.get('LastPart', '0')

    select_part_options = BarCodePUN.objects.filter(
        active=True).order_by('name').values()

    if request.method == 'GET':
        # clear the form
        form = BarcodeScanForm()

    if request.method == 'POST':

        if 'switch-mode' in request.POST:
            context['active_part'] = current_part_id
            return redirect('barcode:duplicate-scan')

        if 'btnsubmit' in request.POST:

            form = BarcodeScanForm(request.POST)

            if form.is_valid():

                barcode = form.cleaned_data.get('barcode')

                current_part_id = int(request.POST.get('part_select', '0'))

                current_part_PUN = BarCodePUN.objects.get(id=current_part_id)

                if not re.search(current_part_PUN.regex, barcode):
                    # malformed barcode
                    context['scanned_barcode'] = barcode
                    context['part_number'] = current_part_PUN.part_number
                    context['expected_format'] = current_part_PUN.regex
                    return render(request, 'barcode/malformed.html', context=context)

                # does barcode exist?
                lm, created = LaserMark.objects.get_or_create(bar_code=barcode)
                if created:
                    # laser mark does not exist in db.  Need to create it.
                    lm.part_number = current_part_PUN.part_number
                    lm.save()

                # has barcode been duplicate scanned?
                dup_scan, created = LaserMarkDuplicateScan.objects.get_or_create(
                    laser_mark=lm)
                if created:
                    # barcode has not been scanned previously
                    messages.add_message(
                        request, messages.ERROR, 'Barcode Not Previously Scanned')
                    dup_scan.delete()
                    form = BarcodeScanForm()
                else:
                    # barcode has already been scanned
                    messages.add_message(
                        request, messages.SUCCESS, f'Barcode Previously Scanned at {dup_scan.scanned_at}')
                    context['status_last'] = 'good'
                    form = BarcodeScanForm()
        else:
            current_part_id = int(request.POST.get('part_select', '0'))
            form = BarcodeScanForm()

    toc = time.time()
    request.session['LastPart'] = current_part_id

    context['form'] = form
    context['title'] = 'Duplicate Scan Check'
    context['scan_check'] = True
    context['active_part'] = int(current_part_id)
    context['part_select_options'] = select_part_options
    context['timer'] = f'{toc-tic:.3f}'

    return render(request, 'barcode/dup_scan.html', context=context)



from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
import random
from .models import LockoutEvent  # Import the LockoutEvent model

def lockout_view(request):
    print("DEBUG: Entered lockout_view")  # Track entry into the view

    # Define locations for all stations where lockout could occur
    locations = ['10R80', '10R60', 'GFX']

    if request.method == 'POST':
        print("DEBUG: POST request received")  # Ensure we hit POST block

        if 'lockout_trigger' in request.POST:
            # This is the initial lockout trigger
            print("DEBUG: Initial lockout trigger received")
            # Get the barcodes from the form
            barcodes = request.POST.get('barcodes', '').split('\n')
            request.session['lockout_barcodes'] = barcodes
            # Generate unlock code
            request.session['unlock_code'] = generate_unlock_code()
            request.session['email_sent'] = False
            # Create LockoutEvent
            lockout_event = LockoutEvent.objects.create(
                unlock_code=request.session['unlock_code'],
                location='Batch Scanner',  # You can dynamically set this based on the actual station
            )
            request.session['lockout_event_id'] = lockout_event.id  # Store the event ID in session
            request.session['lockout_active'] = True
            request.session['unlock_code_submitted'] = False  # Reset this to False
            request.session.modified = True  # Force save session
            print(f"DEBUG: New lockout event, resetting email_sent to False and generating unlock code {request.session['unlock_code']}")
            # Proceed to render the lockout page
        else:
            # This is the supervisor unlock submission
            supervisor_id = request.POST.get('supervisor_id')
            unlock_code = request.POST.get('unlock_code')
            print(f"DEBUG: supervisor_id = {supervisor_id}, unlock_code = {unlock_code}")  # Output form values

            if supervisor_id and unlock_code:
                if unlock_code == request.session.get('unlock_code'):
                    print("DEBUG: Correct unlock code entered")  # Check correct unlock code

                    # Unlock the session by setting the appropriate session flag
                    request.session['lockout_active'] = False
                    request.session['unlock_code_submitted'] = True

                    # Update the LockoutEvent with supervisor_id and unlocked_at
                    lockout_event_id = request.session.get('lockout_event_id')
                    if lockout_event_id:
                        lockout_event = LockoutEvent.objects.get(id=lockout_event_id)
                        lockout_event.supervisor_id = supervisor_id
                        lockout_event.unlocked_at = timezone.now()
                        lockout_event.is_unlocked = True
                        lockout_event.save()

                    print(f"DEBUG: Set lockout_active = {request.session.get('lockout_active')}, unlock_code_submitted = {request.session.get('unlock_code_submitted')}")  # Check session values after unlock

                    # Mark the session as modified to force save
                    request.session.modified = True
                    print("DEBUG: Session modified after successful unlock")  # Confirm session modification

                    # Clear barcodes only after successful unlock, when we're done with the event.
                    if 'lockout_barcodes' in request.session:
                        del request.session['lockout_barcodes']
                        print("DEBUG: Cleared lockout_barcodes from session after successful unlock")

                    messages.success(request, 'Access granted! Returning to the batch scan page.')
                    return redirect('barcode:duplicate_scan_batch')
                else:
                    print("DEBUG: Incorrect unlock code entered")  # Indicate invalid unlock code

                    # Reset lockout and regenerate unlock code
                    request.session['email_sent'] = False
                    request.session['unlock_code'] = generate_unlock_code()  # Generate a new random unlock code

                    # Keep the lockout_barcodes in session
                    print(f"DEBUG: New unlock code generated: {request.session['unlock_code']}")

                    # Update LockoutEvent with new unlock code
                    lockout_event_id = request.session.get('lockout_event_id')
                    if lockout_event_id:
                        lockout_event = LockoutEvent.objects.get(id=lockout_event_id)
                        lockout_event.unlock_code = request.session['unlock_code']
                        lockout_event.save()

                    request.session.modified = True  # Force save session

                    messages.error(request, 'Incorrect unlock code. A new code has been sent.')
            else:
                # Missing supervisor_id or unlock_code
                print("DEBUG: Missing supervisor_id or unlock_code in POST")
                messages.error(request, 'Please enter both supervisor ID and unlock code.')
                # Proceed to render the lockout page with error message

    # Ensure the email gets sent if not already sent
    email_sent_flag = request.session.get('email_sent', False)
    if not email_sent_flag:
        print("DEBUG: Sending lockout email")  # Track request method

        # Get the unlock code from session
        unlock_code = request.session['unlock_code']

        # Get the barcodes from session (updated to handle new barcodes)
        barcodes = [barcode for barcode in request.session.get('lockout_barcodes', []) if barcode.strip()]  # Filter out empty barcodes

        # Email subject with unlock code
        email_subject = f"100% Inspection Hand-Scanner Lockout Notification - Unlock Code: {unlock_code}"

        # HTML email body with details
        email_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; background-color: #f9f9f9; padding: 20px;">

            <div style="background-color: #ffffff; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);">
                <h2 style="color: #d9534f; font-size: 24px; text-align: center;">⚠️ Lockout Alert! ⚠️</h2>

                <p style="font-size: 16px; color: #333;">
                    One or more wrong parts were just scanned and submitted at one of the 100% inspection stations listed below, and immediate investigation is required:
                </p>

                <ul style="font-size: 16px; color: #333; list-style-type: none; padding-left: 0;">
                    <li style="padding: 5px 0;">🔹 {locations[0]}</li>
                    <li style="padding: 5px 0;">🔹 {locations[1]}</li>
                    <li style="padding: 5px 0;">🔹 {locations[2]}</li>
                </ul>

                <p style="font-size: 16px; color: #333;">
                    The following barcodes were scanned:
                </p>

                <ul style="font-size: 16px; color: #333;">
        """

        for barcode in barcodes:
            if barcode.startswith("INVALID:"):
                # Highlight invalid barcodes in red
                clean_barcode = barcode.replace("INVALID:", "")
                email_body += f"<li style='color: red;'>{clean_barcode}</li>"
            else:
                email_body += f"<li>{barcode}</li>"

        email_body += f"""
                </ul>

                <p style="font-size: 16px; color: #333;">
                    Please visit the station to investigate the issue and use the unlock code below to unlock the device:
                </p>

                <h3 style="font-size: 28px; text-align: center; font-weight: bold; padding: 10px 0;">
                    Unlock Code: <span style="font-size: 32px; color: #d9534f;">{unlock_code}</span>
                </h3>

                <p style="font-size: 16px; color: #333; text-align: center;">
                    <em>This code can be used to unlock the device.</em>
                </p>

                <p style="font-size: 14px; color: #777; text-align: center;">
                    <strong>Thank you</strong><br>
                </p>
            </div>

        </body>
        </html>
        """

        # Send the email
        try:
            send_mail(
                email_subject,  # Email subject with unlock code
                '',  # Plain-text version (will be empty since we're using HTML)
                settings.EMAIL_HOST_USER,  # From email
                ['tyler.careless@johnsonelectric.com'],  # To email
                html_message=email_body,  # HTML email content
                fail_silently=False,
            )
            print(f"DEBUG: Email successfully sent to tyler.careless@johnsonelectric.com with unlock code {unlock_code}")

            # Mark that the email has been sent to avoid duplicate emails
            request.session['email_sent'] = True
            request.session.modified = True
            print(f"DEBUG: Set email_sent flag = {request.session.get('email_sent')}")
        except Exception as e:
            print(f"DEBUG: Error occurred while sending email: {e}")

    print(f"DEBUG: Rendering lockout page. lockout_active = {request.session.get('lockout_active')}, unlock_code_submitted = {request.session.get('unlock_code_submitted')}")  # Show session state before rendering page

    return render(request, 'barcode/lockout.html')

# ===============================================
# ===============================================
# ============== Barcode Scan View ==============
# ===============================================
# ===============================================

from django.shortcuts import render, redirect
from django.http import JsonResponse
from .models import LaserMark, LaserMarkDuplicateScan
import MySQLdb
from datetime import timedelta
import time

# Scan view - step 1: Barcode input form
def barcode_scan_view(request):
    if request.method == 'POST':
        barcode_input = request.POST.get('barcode', None)
        if not barcode_input:
            return render(request, 'barcode/barcode_scan.html', {'error': 'No barcode provided'})
        
        # Use LIKE to allow partial matches
        matching_barcodes = LaserMark.objects.filter(bar_code__icontains=barcode_input).order_by('created_at')

        # If multiple matches are found, redirect to the scan pick view
        if matching_barcodes.exists():
            if matching_barcodes.count() > 1:
                # Create list for the next step
                matching_barcodes_list = [
                    {
                        'barcode': barcode.bar_code,
                        'timestamp': barcode.created_at.strftime('%Y-%m-%d (%B %d) %I:%M:%S %p')
                    }
                    for barcode in matching_barcodes
                ]
                return render(request, 'barcode/barcode_matches.html', {'matching_barcodes': matching_barcodes_list})
            else:
                # If only one match, automatically go to results
                return redirect('barcode:barcode-result', barcode=matching_barcodes.first().bar_code)
        else:
            return render(request, 'barcode/barcode_scan.html', {'error': 'No matching barcodes found'})

    return render(request, 'barcode/barcode_scan.html')


# Scan pick view - step 2: Barcode match pick
def barcode_pick_view(request):
    if request.method == 'POST':
        barcode_input = request.POST.get('barcode')
        return redirect('barcode:barcode-result', barcode=barcode_input)

    return redirect('barcode:barcode-scan')


# Results view - step 3: Show barcode result and surrounding barcodes
from django.http import JsonResponse
from django.shortcuts import render
from datetime import timedelta
import MySQLdb
import time

def barcode_result_view(request, barcode):
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        # Handle AJAX request for loading more barcodes (before or after)
        direction = request.POST.get('direction')
        offset = int(request.POST.get('offset', 0))
        batch_size = int(request.POST.get('batch_size', 100))

        try:
            lasermark = LaserMark.objects.get(bar_code=barcode)
        except LaserMark.DoesNotExist:
            return JsonResponse({'error': f'Barcode {barcode} not found'}, status=404)

        if direction == 'before':
            before_barcodes_qs = LaserMark.objects.filter(
                created_at__lt=lasermark.created_at,
                asset=lasermark.asset
            ).order_by('-created_at')

            before_barcodes = before_barcodes_qs[offset:offset + batch_size]
            adjusted_before_barcodes = [
                {'barcode': b.bar_code, 'timestamp': b.created_at.strftime('%Y-%m-%d (%B %d) %I:%M:%S %p')}
                for b in before_barcodes
            ]
            return JsonResponse({'before_barcodes': adjusted_before_barcodes})

        elif direction == 'after':
            after_barcodes_qs = LaserMark.objects.filter(
                created_at__gt=lasermark.created_at,
                asset=lasermark.asset
            ).order_by('created_at')

            after_barcodes = after_barcodes_qs[offset:offset + batch_size]
            adjusted_after_barcodes = [
                {'barcode': a.bar_code, 'timestamp': a.created_at.strftime('%Y-%m-%d (%B %d) %I:%M:%S %p')}
                for a in after_barcodes
            ]
            return JsonResponse({'after_barcodes': adjusted_after_barcodes})

    try:
        # Initial page load: Load 100 barcodes before and after
        lasermark = LaserMark.objects.get(bar_code=barcode)
        lasermark_time = lasermark.created_at.strftime('%Y-%m-%d (%B %d) %I:%M:%S %p')

        # Fetch grade and asset from LaserMark
        grade = lasermark.grade or 'N/A'  # Handle null values with 'N/A'
        asset = lasermark.asset or 'N/A'  # Handle null values with 'N/A'

        # Check for duplicate scan
        try:
            lasermark_duplicate = LaserMarkDuplicateScan.objects.get(laser_mark=lasermark)
            lasermark_duplicate_time = (lasermark_duplicate.scanned_at - timedelta(hours=4)).strftime('%Y-%m-%d (%B %d) %I:%M:%S %p')
        except LaserMarkDuplicateScan.DoesNotExist:
            lasermark_duplicate_time = 'Not found in LaserMarkDuplicateScan'

        # Load initial 100 barcodes before and after
        before_barcodes = LaserMark.objects.filter(
            created_at__lt=lasermark.created_at, 
            asset=lasermark.asset
        ).order_by('-created_at')[:100]

        after_barcodes = LaserMark.objects.filter(
            created_at__gt=lasermark.created_at, 
            asset=lasermark.asset
        ).order_by('created_at')[:100]

        # Format barcodes for display
        adjusted_before_barcodes = [
            {'barcode': b.bar_code, 'timestamp': b.created_at.strftime('%Y-%m-%d (%B %d) %I:%M:%S %p')}
            for b in before_barcodes
        ]
        adjusted_after_barcodes = [
            {'barcode': a.bar_code, 'timestamp': a.created_at.strftime('%Y-%m-%d (%B %d) %I:%M:%S %p')}
            for a in after_barcodes
        ]

        # Query external GP12 database
        barcode_gp12_time = None
        try:
            db = MySQLdb.connect(host="10.4.1.224", user="stuser", passwd="stp383", db="prodrptdb")
            cursor = db.cursor()
            query = "SELECT asset_num, scrap FROM barcode WHERE asset_num = %s"
            cursor.execute(query, (barcode,))
            result = cursor.fetchone()
            if result:
                scrap_time = time.strftime('%Y-%m-%d (%B %d) %I:%M:%S %p', time.gmtime(result[1] - 4 * 3600))
                barcode_gp12_time = scrap_time
            else:
                barcode_gp12_time = "Not found in GP12 database"
            cursor.close()
            db.close()
        except MySQLdb.Error as e:
            barcode_gp12_time = f"Error querying GP12 database: {str(e)}"

        # Prepare context for rendering
        context = {
            'barcode': lasermark.bar_code,
            'grade': grade,
            'asset': asset,
            'lasermark_time': lasermark_time,
            'lasermark_duplicate_time': lasermark_duplicate_time,
            'barcode_gp12_time': barcode_gp12_time,
            'before_barcodes': adjusted_before_barcodes,
            'after_barcodes': adjusted_after_barcodes,
        }

        return render(request, 'barcode/barcode_result.html', context)

    except LaserMark.DoesNotExist:
        return render(request, 'barcode/barcode_scan.html', {'error': f'Barcode {barcode} not found in LaserMark'})









# =====================================================================================
# =====================================================================================
# =========================== Grades Dashboard ========================================
# =====================================================================================
# =====================================================================================

from datetime import datetime, timedelta
from django.db import connections

def fetch_grades_data(part_number, time_interval=720):
    """
    Fetches and structures grade data for a given part number, including total and interval breakdowns.
    
    Args:
        part_number (str): The part number for which data is fetched.
        time_interval (int): The time interval for breakdowns in minutes (default is 720 minutes).
    
    Returns:
        dict: A structured dictionary containing grade data.
    """
    # Define the list of possible grades
    possible_grades = ["A", "B", "C", "D", "E", "F", None]
    
    grade_counts = {}
    total_count = 0
    total_failures = 0  # Track total failures
    breakdown_data = []
    last_24_hours = datetime.now() - timedelta(hours=24)

    try:
        with connections['default'].cursor() as cursor:
            # Query total count for the last 24 hours
            total_query = """
                SELECT COUNT(*)
                FROM barcode_lasermark
                WHERE part_number = %s AND created_at >= %s;
            """
            cursor.execute(total_query, [part_number, last_24_hours])
            total_count = cursor.fetchone()[0]

            # Query counts categorized by grade for the last 24 hours
            grade_query = """
                SELECT grade, COUNT(*)
                FROM barcode_lasermark
                WHERE part_number = %s AND created_at >= %s
                GROUP BY grade;
            """
            cursor.execute(grade_query, [part_number, last_24_hours])
            grade_counts_raw = {row[0]: row[1] for row in cursor.fetchall()}
            
            # Calculate total failures
            total_failures = sum(grade_counts_raw.get(grade, 0) for grade in ["D", "E", "F"])

            # Ensure all possible grades are represented in the 24-hour data
            grade_counts = {
                grade: f"{count} ({round((count / total_count * 100), 2)}%)"
                if total_count > 0 else f"{count} (0.00%)"
                for grade, count in {grade: grade_counts_raw.get(grade, 0) for grade in possible_grades}.items()
            }

            # Generate breakdowns for the past 24 hours based on the given interval
            num_intervals = int((24 * 60) / time_interval)  # Calculate number of intervals
            for interval_offset in range(num_intervals):
                start_time = last_24_hours + timedelta(minutes=interval_offset * time_interval)
                end_time = start_time + timedelta(minutes=time_interval)

                # Query total count for the interval
                interval_total_query = """
                    SELECT COUNT(*)
                    FROM barcode_lasermark
                    WHERE part_number = %s AND created_at >= %s AND created_at < %s;
                """
                cursor.execute(interval_total_query, [part_number, start_time, end_time])
                interval_total_count = cursor.fetchone()[0]

                if interval_total_count == 0:
                    # Skip intervals with zero production
                    continue

                # Query grade counts for the interval
                interval_grade_query = """
                    SELECT grade, COUNT(*)
                    FROM barcode_lasermark
                    WHERE part_number = %s AND created_at >= %s AND created_at < %s
                    GROUP BY grade;
                """
                cursor.execute(interval_grade_query, [part_number, start_time, end_time])
                interval_grade_counts_raw = {row[0]: row[1] for row in cursor.fetchall()}

                # Ensure all possible grades are represented in interval data and calculate percentages
                interval_grade_counts = {
                    grade: f"{count} ({round((count / interval_total_count * 100), 2)}%)"
                    if interval_total_count > 0 else f"{count} (0.00%)"
                    for grade, count in {grade: interval_grade_counts_raw.get(grade, 0) for grade in possible_grades}.items()
                }

                # Append interval data
                breakdown_data.append({
                    "interval_start": start_time.strftime("%Y-%m-%d %H:%M:%S"),
                    "interval_end": end_time.strftime("%Y-%m-%d %H:%M:%S"),
                    "total_count": interval_total_count,
                    "grade_counts": interval_grade_counts
                })
    except Exception as e:
        # Handle exceptions, such as database connection errors
        grade_counts = f"Error retrieving grade counts: {str(e)}"
        total_count = f"Error retrieving total count: {str(e)}"
        breakdown_data = f"Error retrieving interval data: {str(e)}"
        total_failures = f"Error calculating failures: {str(e)}"

    # Build the data dictionary
    return {
        "part_number": part_number,
        "total_count_last_24_hours": total_count,
        "total_failures_last_24_hours": total_failures,
        "grade_counts_last_24_hours": grade_counts,
        "breakdown_data": breakdown_data,
    }



def grades_dashboard(request, part_number, time_interval=60):
    """
    View to render the grades dashboard with Chart.js.
    
    Args:
        request: The HTTP request object.
        part_number (str): The part number for which data is retrieved.
        time_interval (int): The time interval for breakdowns in minutes (default is 720).
    
    Returns:
        HttpResponse: The rendered template with grade data.
    """
    data = fetch_grades_data(part_number, time_interval)
    # Serialize the data to JSON
    json_data = json.dumps(data)
    return render(request, "barcode/grades_dashboard.html", {"json_data": json_data})
