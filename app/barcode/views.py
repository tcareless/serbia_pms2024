import re

from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import connections
import mysql.connector

from barcode.forms import BarcodeScanForm, BatchBarcodeScanForm, BarcodeQueryForm, LaserQueryForm
from barcode.models import LaserMark, LaserMarkDuplicateScan, BarCodePUN
import time

import logging
logger = logging.getLogger(__name__)

from query_tracking.models import record_execution_time

def laser_count(request):
    context = {}
    form = LaserQueryForm()
    context['form'] = form
    if request.method == "POST":
        laser_form = LaserQueryForm(data=request.POST)
        if laser_form.is_valid():
            asset = laser_form.cleaned_data['asset']
            start_date = laser_form.cleaned_data['start_date']
            end_date = laser_form.cleaned_data['end_date']
            
            db_params = {'host': '10.4.1.245',
                        'database': 'django_pms',
                        'port': 6601,
                        'user': 'muser',
                        'password': 'wsj.231.kql'}

            tic = time.time()
            sql = f"select\n"
            sql += f"count(*) as count,\n"
            sql += f"date(created_at) as date,\n"
            sql += f"grade\n"
            sql += f"from `barcode_lasermark`\n"
            sql += f"where\n"
            sql += f"asset={asset} AND date(created_at) between '{start_date.strftime('%Y-%m-%d')}' AND '{end_date.strftime('%Y-%m-%d')}'\n"
            sql += f"group by date, grade\n"
            sql += f"order by date, grade;"
            try:
                connection = mysql.connector.connect(**db_params)
                cursor = connection.cursor(dictionary=True)
                cursor.execute(sql)
                results = []
                row = cursor.fetchone()
                last = row['date']
                while row:
                    row = cursor.fetchone()
                    if row != None:
                        if last != row['date']:
                            results[-1]['div'] = True
                        last = row['date']
                        results.append(row)
                context['result'] = results
                context['asset'] = asset
            except:
                context['error'] = "Query failed"
            toc = time.time()
            record_execution_time("laser_count", sql, toc-tic)
            context['time'] = f'Elapsed: {toc-tic:.3f} seconds'

    return render(request, 'barcode/laser_count.html', context=context)

def query(request):
    context = {}
    form = BarcodeQueryForm()
    context['form'] = form
    if request.method == "POST":
        barcode_form = BarcodeQueryForm(data=request.POST)
        if barcode_form.is_valid():
            barcode = barcode_form.cleaned_data['barcode']
            
            tic = time.time()
            sql = ""
            try:
                lasermark = LaserMark.objects.get(bar_code = barcode)
                results = []
                results.append(lasermark)
                above = LaserMark.objects.filter(id__gt=lasermark.id, asset = lasermark.asset).reverse()[:20]
                sql += above.query.__str__()
                below = LaserMark.objects.filter(id__lt=lasermark.id, asset = lasermark.asset)[:20]
                sql += "\n"
                sql += below.query.__str__()
                for row in above:
                    results.append(row)
                for row in below:
                    results.append(row)
                results.sort(key=lambda r: r.id, reverse=True)
                context['result'] = results
            except:
                context['error'] = "Query failed"
            toc = time.time()
            record_execution_time("query", sql, toc-tic)
            context['time'] = f'Elapsed: {toc-tic:.3f} seconds'

    return render(request, 'barcode/query.html', context=context)

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
    if request.method == 'GET':
        # clear the form
        form = BatchBarcodeScanForm()

    if request.method == 'POST':

        if 'btnsubmit' in request.POST:
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
                    if barcode['status'] == 'failed_grade':
                        context['scanned_barcode'] = barcode
                        context['part_number'] = current_part_PUN.part_number
                        context['grade'] = barcode['grade']
                        return render(request, 'barcode/failed_grade.html', context=context)

                    # barcode has already been scanned
                    if barcode['status'] == 'duplicate':
                        context['scanned_barcode'] = barcode['barcode']
                        context['part_number'] = barcode['part_number']
                        context['duplicate_scan_at'] = barcode['scanned_at']
                        return render(request, 'barcode/dup_found.html', context=context)

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
