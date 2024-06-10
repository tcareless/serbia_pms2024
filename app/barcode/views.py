import datetime
import json

import re
from django.utils import timezone

from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse

from barcode.forms import BarcodeScanForm, BatchBarcodeScanForm
from barcode.models import LaserMark, LaserMarkDuplicateScan, BarCodePUN
import time

from django.urls import reverse
from .email_config import generate_and_send_code
import random


import logging


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


def duplicate_scan(request):
    context = {}
    tic = time.time()  # Start timer for processing time measurement
    running_count = int(request.session.get('RunningCount', '0'))  # Retrieve the current running count from session
    last_part_id = request.session.get('LastPartID', '0')  # Retrieve the last part ID from session
    current_part_id = last_part_id  # Set the current part ID to the last part ID

    # Get active part options from the database, ordered by name
    select_part_options = BarCodePUN.objects.filter(active=True).order_by('name').values()

    if request.method == 'GET':
        form = BarcodeScanForm()  # Initialize an empty form for GET request

    if request.method == 'POST':
        if 'switch-mode' in request.POST:
            # If switch mode is requested, redirect to duplicate scan check
            context['active_part'] = current_part_id
            return redirect('barcode:duplicate-scan-check')

        if 'set_count' in request.POST:
            # If set count is requested, reset the running count and reinitialize the form
            messages.add_message(request, messages.INFO, 'Count reset.')
            running_count = request.POST.get('count', 0) or 0
            running_count = int(running_count)
            form = BarcodeScanForm()

        elif 'btnsubmit' in request.POST:
            # Handle form submission for barcode scanning
            form = BarcodeScanForm(request.POST)

            if form.is_valid():
                barcode = form.cleaned_data.get('barcode')  # Get the scanned barcode
                current_part_id = int(request.POST.get('part_select', '0'))  # Get the selected part ID
                current_part_PUN = BarCodePUN.objects.get(id=current_part_id)  # Get the part details

                # Validate the barcode format against the expected regex pattern
                if not re.search(current_part_PUN.regex, barcode):
                    context['scanned_barcode'] = barcode
                    context['part_number'] = current_part_PUN.part_number
                    context['expected_format'] = current_part_PUN.regex
                    return render(request, 'barcode/malformed.html', context=context)

                # Check if the barcode already exists in the database
                lm, created = LaserMark.objects.get_or_create(bar_code=barcode)
                if created:
                    lm.part_number = current_part_PUN.part_number
                    lm.save()  # Save the new LaserMark object

                # Check the grade of the LaserMark
                if lm.grade not in ('A', 'B', 'C'):
                    context['scanned_barcode'] = barcode
                    context['part_number'] = lm.part_number
                    context['grade'] = lm.grade
                    return render(request, 'barcode/failed_grade.html', context=context)

                # Check for duplicate scans of the LaserMark
                dup_scan, created = LaserMarkDuplicateScan.objects.get_or_create(laser_mark=lm)
                if not created:
                    # If duplicate scan found, generate and send an unlock code
                    unlock_code = generate_and_send_code()
                    request.session['unlock_code'] = unlock_code
                    request.session['duplicate_found'] = True
                    request.session['unlock_code_submitted'] = False
                    request.session['duplicate_barcode'] = barcode
                    request.session['duplicate_part_number'] = lm.part_number
                    request.session['duplicate_scan_at'] = str(dup_scan.scanned_at)
                    print("Duplicate found: True")
                    print("Unlock code: ", request.session.get('unlock_code'))
                    return redirect('barcode:duplicate-found')
                else:
                    dup_scan.save()  # Save the new duplicate scan record
                    messages.add_message(request, messages.SUCCESS, 'Valid Barcode Scanned')
                    running_count += 1  # Increment the running count
                    request.session['LastPartID'] = current_part_id  # Update the last part ID in session
                    form = BarcodeScanForm()  # Reinitialize the form
        else:
            current_part_id = int(request.POST.get('part_select', '0'))  # Get the selected part ID
            running_count = 0  # Reset the running count
            form = BarcodeScanForm()  # Reinitialize the form

    toc = time.time()  # End timer for processing time measurement
    request.session['RunningCount'] = running_count  # Update the running count in session

    # Set context variables for rendering the template
    context['form'] = form
    context['running_count'] = running_count
    context['title'] = 'Duplicate Scan'
    context['scan_check'] = False
    context['active_part'] = current_part_id
    context['part_select_options'] = select_part_options
    context['timer'] = f'{toc-tic:.3f}'

    return render(request, 'barcode/dup_scan.html', context=context)


def duplicate_found_view(request):
    # Check if unlock code is already in session, if not, generate and send a new one
    if 'unlock_code' not in request.session:
        request.session['unlock_code'] = generate_and_send_code()

    if request.method == 'POST':
        # Retrieve the submitted unlock code from the form
        submitted_code = request.POST.get('unlock_code')
        
        # Check if the submitted code matches the one in the session
        if submitted_code == request.session.get('unlock_code'):
            # If correct, set unlock_code_submitted to True and reset duplicate_found
            request.session['unlock_code_submitted'] = True
            request.session['duplicate_found'] = False
            return redirect('barcode:duplicate-scan')
        else:
            # If incorrect, show an error message
            messages.error(request, 'Invalid unlock code. Please try again.')

    # Prepare context data for the template
    context = {
        'scanned_barcode': request.session.get('duplicate_barcode', ''),
        'part_number': request.session.get('duplicate_part_number', ''),
        'duplicate_scan_at': request.session.get('duplicate_scan_at', ''),
        'unlock_code': request.session.get('unlock_code'),
    }
    
    # Render the template with the context data
    return render(request, 'barcode/dup_found.html', context=context)

def send_new_unlock_code(request):
    # Generate a new unlock code and send it via email
    unlock_code = generate_and_send_code()
    
    # Store the new unlock code in the session
    request.session['unlock_code'] = unlock_code
    request.session['duplicate_found'] = True  # Indicate that a duplicate was found
    request.session['unlock_code_submitted'] = False  # Reset the unlock code submission status
    
    # Log the generated unlock code for debugging purposes
    print(f"Generated unlock code: {unlock_code}")
    
    # Redirect the user to the duplicate-found page
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
