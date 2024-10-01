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
                messages.error(request, 'Invalid unlock code. Please try again.')

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

                    # # get or create a laser-mark for the scanned code
                    # processed_barcodes.append(
                    #     verify_barcode(current_part_id, barcode))
                    # # print(f'{current_part_PUN.part_number}:{barcode}')
                    pass

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

    # Ensure the user is locked out
    if not request.session.get('lockout_active', False):
        # New lockout event, reset email_sent and generate a new unlock code
        request.session['email_sent'] = False
        request.session['unlock_code'] = generate_unlock_code()  # Generate a new random unlock code

        # Create a new LockoutEvent and save it in the database
        lockout_event = LockoutEvent.objects.create(
            unlock_code=request.session['unlock_code'],
            location='Batch Scanner',  # You can dynamically set this based on the actual station
        )
        request.session['lockout_event_id'] = lockout_event.id  # Store the event ID in session

        print(f"DEBUG: New lockout event, resetting email_sent to False and generating unlock code {request.session['unlock_code']}")

    request.session['lockout_active'] = True
    request.session['unlock_code_submitted'] = False  # Reset this to False
    request.session.modified = True  # Force save session
    print(f"DEBUG: Set lockout_active = {request.session.get('lockout_active')}, reset unlock_code_submitted = {request.session.get('unlock_code_submitted')}")  # Check session values

    # Static locations for all stations where lockout could occur
    locations = ['10R80', '10R60', 'GFX']

    # Track the value of the email_sent flag before deciding to send the email
    email_sent_flag = request.session.get('email_sent', False)
    print(f"DEBUG: email_sent flag before processing = {email_sent_flag}")  # Track current email_sent flag

    # Only send the email on the first GET request (when user lands on the page)
    if request.method == 'GET':
        print("DEBUG: Processing GET request")  # Track request method

        # Send email if it hasn't been sent yet
        if not email_sent_flag:
            print("DEBUG: GET request received, sending email to supervisor")

            # Get the unlock code from session
            unlock_code = request.session['unlock_code']

            # Email subject with unlock code
            email_subject = f"100% inspection Hand-Scanner Lockout Notification - Unlock Code: {unlock_code}"

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
        else:
            print("DEBUG: Email has already been sent, skipping email sending")

    if request.method == 'POST':
        print("DEBUG: POST request received")  # Ensure we hit POST block
        supervisor_id = request.POST.get('supervisor_id')
        unlock_code = request.POST.get('unlock_code')
        print(f"DEBUG: supervisor_id = {supervisor_id}, unlock_code = {unlock_code}")  # Output form values
        
        # Verify if the unlock code matches the one stored in the session
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

            messages.success(request, 'Access granted! Returning to the batch scan page.')
            return redirect('barcode:duplicate_scan_batch')
        else:
            print("DEBUG: Incorrect unlock code entered")  # Indicate invalid unlock code
            messages.error(request, 'Invalid unlock code. Please try again.')

    # Display lockout page
    print(f"DEBUG: Rendering lockout page. lockout_active = {request.session.get('lockout_active')}, unlock_code_submitted = {request.session.get('unlock_code_submitted')}")  # Show session state before rendering page

    return render(request, 'barcode/lockout.html')







# ==========================================================
# ==========================================================
# ========= Daily Email Scan Differential API Endpoint =====
# ==========================================================
# ==========================================================

from django.shortcuts import render
from django.utils import timezone
from django.db.models import Count
from .models import LaserMarkDuplicateScan
import mysql.connector
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.http import HttpResponse

def parts_scanned_last_24_hours(request):
    # Get the current time in the server's timezone
    now = timezone.now()
    now_epoch = int(now.timestamp())

    # Calculate 2 AM two nights ago
    two_nights_ago_2am = (now - timezone.timedelta(days=2)).replace(hour=2, minute=0, second=0, microsecond=0)
    end_time = two_nights_ago_2am + timezone.timedelta(hours=24)

    # Define the start times for shifts within this 24-hour window
    shift1_start = two_nights_ago_2am
    shift2_start = shift1_start + timezone.timedelta(hours=8)
    shift3_start = shift2_start + timezone.timedelta(hours=8)

    # List of part numbers to filter, grouped by machine
    part_numbers_to_machines = {
        '1617': ['50-9641G', '50-4865F', '50-4865G'],
        '1533': ['50-9341F', '50-9341G'],
        '1816': ['50-0455F', '50-0455G']
    }

    # Flatten part numbers for filtering
    part_numbers = [pn for pns in part_numbers_to_machines.values() for pn in pns]

    # Filter LaserMarkDuplicateScan entries within this 24-hour window
    duplicate_scans = LaserMarkDuplicateScan.objects.filter(
        scanned_at__gte=two_nights_ago_2am,
        scanned_at__lt=end_time,
        laser_mark__part_number__in=part_numbers
    )

    # Helper function to group by machine
    def group_by_machine(shift_scans):
        machine_counts = {}
        for machine, parts in part_numbers_to_machines.items():
            count = shift_scans.filter(laser_mark__part_number__in=parts).count()
            machine_counts[machine] = count
        return machine_counts

    # Split the scans by shifts and group them by machine
    shift1_scans = duplicate_scans.filter(scanned_at__gte=shift1_start, scanned_at__lt=shift2_start)
    shift2_scans = duplicate_scans.filter(scanned_at__gte=shift2_start, scanned_at__lt=shift3_start)
    shift3_scans = duplicate_scans.filter(scanned_at__gte=shift3_start, scanned_at__lt=end_time)

    shift_data = {
        'shift1': group_by_machine(shift1_scans),
        'shift2': group_by_machine(shift2_scans),
        'shift3': group_by_machine(shift3_scans)
    }

    # Connect to the MySQL database
    db_config = {
        'user': 'stuser',
        'password': 'stp383',
        'host': '10.4.1.245',
        'database': 'prodrptdb',
    }
    connection = mysql.connector.connect(**db_config)
    cursor = connection.cursor()

    # Adjust start time for MySQL queries to match the two_nights_ago_2am
    start_time = int(two_nights_ago_2am.timestamp())  # Convert to UNIX timestamp

    # Function to execute the shift count query for a given machine
    def get_shift_counts(machine):
        query = f"""
        SELECT
            SUM(CASE WHEN TimeStamp >= {start_time} AND TimeStamp < {start_time} + 28800 THEN 1 ELSE 0 END) as shift1,
            SUM(CASE WHEN TimeStamp >= {start_time} + 28800 AND TimeStamp < {start_time} + 57600 THEN 1 ELSE 0 END) as shift2,
            SUM(CASE WHEN TimeStamp >= {start_time} + 57600 AND TimeStamp < {start_time} + 86400 THEN 1 ELSE 0 END) AS shift3
        FROM `GFxPRoduction`
        WHERE TimeStamp >= {start_time} AND TimeStamp < {start_time} + 86400
        AND `Machine` = '{machine}';
        """
        cursor.execute(query)
        return cursor.fetchone()

    # Get shift counts for each machine
    machines = ['1617', '1533', '1816']
    gfx_data = {}
    for machine in machines:
        gfx_data[machine] = get_shift_counts(machine)

    # Close the database connection
    cursor.close()
    connection.close()

    # Function to calculate percentage difference
    def calculate_percentage_difference(laser_mark_count, gfx_count):
        if gfx_count == 0:
            return 0
        return round(((laser_mark_count - gfx_count) / gfx_count) * 100, 1)

    # Prepare data per machine per shift
    data = {}
    for machine in machines:
        data[machine] = {}
        for i, shift in enumerate(['shift1', 'shift2', 'shift3']):
            gfx_count = gfx_data[machine][i] if gfx_data[machine][i] is not None else 0
            laser_mark_count = shift_data[shift][machine]
            difference = abs(gfx_count - laser_mark_count)
            percentage_difference = calculate_percentage_difference(laser_mark_count, gfx_count)
            data[machine][shift] = {
                'gfx': gfx_count,
                'laser_mark_scanned': laser_mark_count,
                'difference': difference,
                'percentage_difference': percentage_difference
            }

    # Render the template to a string
    html_content = render_to_string('barcode/parts_scanned_last_24_hours.html', {'data': data})

    # Prepare email parameters
    subject = 'Parts Scanned in the Last Day'
    from_email = 'noreply@johnsonelectric.com'  # Ensure this matches DEFAULT_FROM_EMAIL
    recipient_list = ['tyler.careless@johnsonelectric.com', 'testmailer@gmail.com']

    # Create email message
    email = EmailMessage(
        subject=subject,
        body=html_content,
        from_email=from_email,
        to=recipient_list,
    )
    email.content_subtype = 'html'  # Set the content type to HTML

    # Send the email
    try:
        email.send()
        # Return an HTTP response indicating success
        return HttpResponse('Email sent successfully.')
    except Exception as e:
        # Handle exceptions and return an error response
        return HttpResponse(f'Error sending email: {e}', status=500)




