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
        print(request.POST)
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

                    # get or create a laser-mark for the scanned code
                    processed_barcodes.append(
                        verify_barcode(current_part_id, barcode))
                    # print(f'{current_part_PUN.part_number}:{barcode}')

                for barcode in processed_barcodes:

                    # Malformed Barcode
                    if barcode['status'] == 'malformed':
                        print('Malformed Barcode')
                        context['scanned_barcode'] = barcode
                        context['part_number'] = current_part_PUN.part_number
                        context['expected_format'] = current_part_PUN.regex
                        return render(request, 'barcode/malformed.html', context=context)

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
