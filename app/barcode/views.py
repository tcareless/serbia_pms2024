import json

import re
from django.utils import timezone

from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse

from barcode.forms import BarcodeScanForm
from barcode.models import LaserMark, LaserMarkDuplicateScan, BarCodePUN
import time

import logging
logger = logging.getLogger(__name__)


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


# def verify_barcode(request, part, barcode):
def verify_barcode(request):
    context = {}

    if request.method == 'POST' and request.headers.get("contentType", "application/json"):
        body_unicode = request.body.decode('utf-8')
        received_json = json.loads(body_unicode)
        print(received_json)
        current_part_PUN = BarCodePUN.objects.get(id=received_json['part_select'])
        if not re.search(current_part_PUN.regex, received_json['code']):
            print('Malformed Barcode')
            # malformed barcode
            context['scanned_barcode'] = received_json['code']
            context['part_number'] = current_part_PUN.part_number
            context['expected_format'] = current_part_PUN.regex
            # Doesn't work, needs signaled and triggered in javascript?
            # return render(request, 'barcode/malformed.html', context=context)

    # logger.info(f'{part}:{barcode}')

    # data = {'part': part, 'barcode': barcode, 'result': "good"}

    # logger.info(f'{part}:{barcode}:{data.get("result")}')
    #return JsonResponse(data)
    return JsonResponse({"worked": "true", "ex": current_part_PUN.regex})

def duplicate_scan(request):
    context = {}
    tic = time.time()
    # get data from session
    running_count = int(request.session.get('RunningCount', '0'))
    last_part_id = request.session.get('LastPartID', '0')
    # initialize current_part_id if no barcode submitted
    current_part_id = last_part_id

    # set lm to None to prevent error
    lm = None

    select_part_options = BarCodePUN.objects.filter(
        active=True).order_by('name').values()

    if request.method == 'GET':
        # clear the form
        form = BarcodeScanForm()

    if request.method == 'POST':

        if 'switch-mode' in request.POST:
            context['active_part'] = current_part_id
            return redirect('duplicate-scan-check')

        if 'set_count' in request.POST:
            messages.add_message(request, messages.INFO, 'Count reset.')
            running_count = request.POST.get('count', 0) or 0
            running_count = int(running_count)
            form = BarcodeScanForm()

        elif 'btnsubmit' in request.POST:
            form = BarcodeScanForm(request.POST)

            if form.is_valid():
                # get or create a laser-mark for the scanned code
                barcode = form.cleaned_data.get('barcode')

                current_part_id = int(request.POST.get('part_select', '0'))
                current_part_PUN = BarCodePUN.objects.get(id=current_part_id)

                if not re.search(current_part_PUN.regex, barcode):
                    print('Malformed Barcode')
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
                if lm.grade not in ('A', 'B', 'C'):
                    context['scanned_barcode'] = barcode
                    context['part_number'] = lm.part_number
                    context['grade'] = lm.grade
                    return render(request, 'barcode/failed_grade.html', context=context)

                # has barcode been duplicate scanned?
                dup_scan, created = LaserMarkDuplicateScan.objects.get_or_create(
                    laser_mark=lm)
                if not created:
                    # barcode has already been scanned
                    context['scanned_barcode'] = barcode
                    context['part_number'] = lm.part_number
                    context['duplicate_scan_at'] = dup_scan.scanned_at
                    return render(request, 'barcode/dup_found.html', context=context)

                else:
                    # barcode has not been scanned previously
                    dup_scan.save()
                    # pass data to the template
                    messages.add_message(
                        request, messages.SUCCESS, 'Valid Barcode Scanned')
                    running_count += 1

                    # use the session to track the last successfully scanned part type
                    # to detect part type changes and reset the count
                    request.session['LastPartID'] = current_part_id

                    # clear the form data for the next one
                    form = BarcodeScanForm()

                print(f'{current_part_PUN.part_number}:{running_count}, {barcode}')
        else:
            current_part_id = int(request.POST.get('part_select', '0'))
            running_count = 0
            form = BarcodeScanForm()

    toc = time.time()
    # use the session to maintain a running count of parts per user
    request.session['RunningCount'] = running_count

    # context['last_part_status'] = last_part_status
    context['form'] = form
    context['running_count'] = running_count
    context['title'] = 'Duplicate Scan'
    context['scan_check'] = False
    context['active_part'] = current_part_id
    context['part_select_options'] = select_part_options
    context['timer'] = f'{toc-tic:.3f}'

    return render(request, 'barcode/dup_scan.html', context=context)


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
            return redirect('duplicate-scan')

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
