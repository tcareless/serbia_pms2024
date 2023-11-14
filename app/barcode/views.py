from datetime import datetime
from django.db.models import Count
import json

import re
from django.utils import timezone

from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q

from barcode.forms import BarcodeScanForm, BatchBarcodeScanForm, LasermarkSearchForm
from barcode.models import LaserMark, LaserMarkDuplicateScan, BarCodePUN
import time

import logging
logger = logging.getLogger(__name__)




def search_totals(part_total_dict, part_number):
    for x in range(0,len(part_total_dict)):
        if part_total_dict[x]['part_number'] == part_number:
            return part_total_dict[x]['part_count']
        
    
        
    


def lasermark_table_view(request):
    found_lasermarks = []
    rows = []
    form = LasermarkSearchForm()
    

    if request.method == "POST":
        #handle form data, send back context to display
        form = LasermarkSearchForm(request.POST)

        if form.is_valid():
            
            search_asset = form.cleaned_data.get('asset_number')
            search_start = form.cleaned_data.get('time_start')
            search_end = form.cleaned_data.get('time_end')
            
        part_quantity_by_grade = LaserMark.objects \
            .filter(asset=search_asset, created_at__gt=search_start, created_at__lt=search_end) \
            .values('part_number', 'grade') \
            .annotate(part_count=Count('part_number')) \
            .order_by('part_number', 'grade')
        
        total_parts_for_part_number = LaserMark.objects\
            .filter(asset=search_asset, created_at__gt=search_start, created_at__lt=search_end) \
            .values('part_number') \
            .annotate(part_count=Count('part_number')) \
            .order_by('part_number')
        
        list_of_part_numbers = part_quantity_by_grade.values_list('part_number', flat=True).distinct().order_by()
        
        

        master_list = []
        this_list = []
        this_part_number = ''
        this_total = 0.0
        this_percent = 0.0
        part_grade_index = {"A": 1, "B": 3, "C": 5, "D": 7, "E": 9, "F": 11, "G": 13}
        part_percent_index = {"A": 2, "B": 4, "C": 6, "D": 8, "E": 10, "F": 12, "G": 14}

        for part in part_quantity_by_grade:
            if part['part_number'] == None or part['grade'] == None:
                pass
            else:
                if this_part_number == '':
                    this_part_number = part['part_number']
                    this_list = [this_part_number,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
                    this_grade_index = part_grade_index[part['grade']]
                    this_percent_index = part_percent_index[part['grade']]
                    this_list[this_grade_index] = part['part_count']
                    #make function to find total part amount
                    this_total = search_totals(total_parts_for_part_number, part['part_number'])
                    this_percent = round((part['part_count'] / this_total) * 100, 2)
                    this_list[this_percent_index] = this_percent
                elif part['part_number'] != this_part_number:
                    master_list.append(this_list)
                    this_part_number = part['part_number']
                    this_list = [this_part_number,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
                    this_grade_index = part_grade_index[part['grade']]
                    this_percent_index = part_percent_index[part['grade']]
                    this_list[this_grade_index] = part['part_count']
                    #make function to find total part amount
                    this_total = search_totals(total_parts_for_part_number, part['part_number'])
                    this_percent = round((part['part_count'] / this_total) * 100, 2)
                    this_list[this_percent_index] = this_percent

                    

                elif part['part_number'] == this_part_number:
                    #just get the count and percentage
                    this_grade_index = part_grade_index[part['grade']]
                    this_percent_index = part_percent_index[part['grade']]
                    this_list[this_grade_index] = part['part_count']
                    #make function to find total part amount
                    this_total = search_totals(total_parts_for_part_number, part['part_number'])
                    this_percent = round((part['part_count'] / this_total) * 100, 2)
                    this_list[this_percent_index] = this_percent

                    


        #add last this_list that wasn't added in the loop
        master_list.append(this_list)

        #convert the list to the view needed for the template
        new_list = []
        rows_for_template = []
        for row in master_list:
            for x in range(0,len(row)):
                if x == 0:
                    #if part number
                    new_list.append(row[x])
                elif x % 2 != 0:
                    #if odd
                    new_list.append(str(row[x+1])+"% ("+str(row[x])+" pcs)")
                elif x == (len(row)-1):
                    rows_for_template.append(new_list)
                    new_list = []


        


        
   
        context = {
            'rows' : rows_for_template,
            'laser_form' : form,
        }

    else:
        #it's a get request
        context = {
            'rows' : [],
            'laser_form' : form,
            
        }

    
    
    return render(request, f'barcode/lasermark_table.html', context)



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
            return redirect('barcode:duplicate-scan-check')

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
