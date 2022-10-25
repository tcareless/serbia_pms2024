import re
from django.utils import timezone

from django.shortcuts import render
from django.contrib import messages

from barcode.forms import BarcodeScanForm
from barcode.models import LaserMark, BarCodePUN


"""
Quality Scanning:
This code provides a check that barcodes are valid for the current part number.  
Parts are scanned as needed (first off etc).  The scan is automatically submitted by pressing enter.  The scanner 
automatically adds Enter to the end of the scanned barcode.  
The scan is verified to contain the correct data for the part type and that all variable sections contain sane data.  
If any of the data is no good, an error screen is displayed to the operator.  
The the time and date of the scan is saved in the database in the quality column.  If the same barcode is scanned 
again, the quality column is updated.  If the barcode does not exist in the database, it is added with a creation 
time of now.  
If the barcode is valid, the screen refreshes so the operator can enter the next code. 
Querying if any checks were done in a give time period provides a way to audit if checks are being completed properly.
"""

def quality_scan(request):

    select_part_options = BarCodePUN.objects.all()  # *TODO BarCodePun.objects.fileter(active=True)

    if request.method == 'GET':
        # clear the form
        form = BarcodeScanForm()
        current_part_id = request.session.get('LastPart', 0)

    if request.method == 'POST':
        form = BarcodeScanForm(request.POST)

        current_part_id = int(request.POST.get('part_select', '0'))

        if form.is_valid():

            # get or create a laser-mark for the scanned code
            barcode = form.cleaned_data.get('barcode')
            current_part_PUN = BarCodePUN.objects.get(id=current_part_id)

            # lm, created = LaserMark.objects.get_or_create(bar_code=barcode)

            try:
                lm = LaserMark.objects.get(bar_code=barcode)
            except LaserMark.DoesNotExist:
                lm = LaserMark(bar_code=barcode)

            # set the part number if not previously set
            if not lm.part_number:
                lm.part_number = current_part_PUN.part_number

            if re.search(current_part_PUN.regex, barcode):
                # good barcode format
                lm.quality_scan_at = timezone.now()
                lm.save()
                messages.add_message(request, messages.SUCCESS, 'Valid Barcode Scanned')
                form = BarcodeScanForm()

            else:
                # barcode is not correctly formed
                # lm.delete()

                # save the current part id over error screens
                request.session['LastPart'] = current_part_id

                context = {
                    'scanned_barcode': barcode,
                    'part_number': current_part_PUN.part_number,
                    'expected_format': current_part_PUN.regex,
                }
                return render(request, 'barcode/malformed.html', context=context)

    context = {
        'form': form,
        'title': 'Barcode Quality Scan',
        'active_part': current_part_id,
        'part_select_options': select_part_options,
    }

    return render(request, 'barcode/quality_scan.html', context=context)


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
"""


def duplicate_scan(request):
    #  print(f"request.Post={request.POST}")
    #  print(f"request.session.session_key={request.session.session_key}")
    #  print(dir(request.session))

    # get data from session
    running_count = int(request.session.get('RunningCount', '0'))
    last_part_id = request.session.get('LastPart', '0')
    # initialize current_part_id if no barcode submitted
    current_part_id = last_part_id

    # used to tell the template to display error screens
    last_part_status = None

    # set lm to None to prevent error
    lm = None

    select_part_options = BarCodePUN.objects.all()  # *TODO BarCodePun.objects.fileter(active=True)

    if request.method == 'GET':
        # clear the form
        form = BarcodeScanForm()

    if request.method == 'POST':

        if 'set_count' in request.POST:
            messages.add_message(request, messages.INFO, 'Count reset.')
            running_count = int(request.POST.get('count', 0) or 0)
            form = BarcodeScanForm()


        if 'submit' in request.POST:
            form = BarcodeScanForm(request.POST)

            # reset counter to 0 if part type changes
            current_part_id = int(request.POST.get('part_select', '0'))
            if not current_part_id == last_part_id:
                running_count = 0

            if form.is_valid():

                # get or create a laser-mark for the scanned code
                barcode = form.cleaned_data.get('barcode')
                lm, created = LaserMark.objects.get_or_create(bar_code=barcode)
                #        print(lm.created_at, lm.duplicate_scan_at)

                if lm.duplicate_scan_at:
                    # barcode has already been scanned
                    context = {
                        'scanned_barcode': barcode,
                        'part_number': lm.part_number,
                        'duplicate_scan_at': lm.duplicate_scan_at,
                    }
                    return render(request, 'barcode/dup_found.html', context=context)

                else:
                    # barcode has not been scanned previously
                    current_part_PUN = BarCodePUN.objects.get(id=current_part_id)

                    # set the part number if not previously set
                    if not lm.part_number:
                        lm.part_number = current_part_PUN.part_number

                    if re.search(current_part_PUN.regex, barcode):
                        # good barcode format
                        lm.duplicate_scan_at = timezone.now()
                        lm.save()

                        # pass data to the template
                        messages.add_message(request, messages.SUCCESS, 'Valid Barcode Scanned')
                        running_count += 1
                        # clear the form data for the next one
                        form = BarcodeScanForm()
                    else:
                        # barcode is not correctly formed
                        lm.delete()
                        context = {
                            'scanned_barcode': barcode,
                            'part_number': current_part_PUN.part_number,
                            'expected_format': current_part_PUN.regex,
                        }
                        return render(request, 'barcode/malformed.html', context=context)

    # use the session to maintain a running count of parts per user
    request.session['RunningCount'] = running_count

    # use the session to track the last successfully scanned part type
    # to detect part type changes and reset the count
    request.session['LastPart'] = current_part_id

    context = {
        'last_part_status': last_part_status,
        'form': form,
        'running_count': running_count,
        'title': 'Barcode Scan',
        'active_part': current_part_id,
        'part_select_options': select_part_options,
    }

    return render(request, 'barcode/dup_scan.html', context=context)
