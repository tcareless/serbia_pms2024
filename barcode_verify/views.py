import re
from django.utils import timezone

from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib import messages
from django.db import IntegrityError

from barcode_verify.forms import VerifyBarcodeForm
from barcode_verify.models import LaserMark, BarCodePUN


def dup_scan(request):
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
        form = VerifyBarcodeForm()

    if request.method == 'POST':

        if 'set_count' in request.POST:
            messages.add_message(request, messages.INFO, 'Count reset.')
            running_count = int(request.POST.get('count', 0) or 0)

        if 'submit' in request.POST:
            form = VerifyBarcodeForm(request.POST)

            # reset counter to 0 if part type changes
            current_part_id = int(request.POST.get('part_select', '0'))
            if not current_part_id == last_part_id:
                running_count = 0

            if form.is_valid():

                # get or create a laser-mark for the scanned code
                bar_code = form.cleaned_data.get('barcode')
                lm, created = LaserMark.objects.get_or_create(bar_code=bar_code)
                #        print(lm.created_at, lm.scanned_at)

                if lm.scanned_at:
                    # barcode has already been scanned
                    context = {
                        'last_part_status': 'duplicate-barcode',
                        'last_barcode': lm,
                        'form': form,
                        'running_count': running_count,
                        'active_part': current_part_id,
                    }
                    return render(request, 'barcode_verify/dup_found.html', context=context)

                else:
                    # barcode has not been scanned previously
                    current_part_PUN = BarCodePUN.objects.get(id=current_part_id)

                    # set the part number in not previously set
                    if not lm.part_number:
                        lm.part_number = current_part_PUN.part_number

                    if re.search(current_part_PUN.regex, bar_code):
                        # good barcode format
                        lm.scanned_at = timezone.now()
                        lm.save()

                        # pass data to the template
                        messages.add_message(request, messages.SUCCESS, 'Valid Barcode Scanned')
                        running_count += 1
                        last_part_status = 'ok'
                        # clear the form data for the next one
                        form = VerifyBarcodeForm()
                    else:
                        # barcode is not correctly formed
                        context = {
                            'last_part_status': 'barcode-malformed',
                            'last_barcode': lm,
                            'form': form,
                            'running_count': running_count,
                            'title': 'Duplicat Barcode Found',
                            'active_part': current_part_id,
                        }
                        return render(request, 'barcode_verify/malformed.html', context=context)

    # use the session to maintain a running count of parts per user
    request.session['RunningCount'] = running_count

    # use the session to track the last successfully scanned part type
    # to detect part type changes and reset the count
    request.session['LastPart'] = current_part_id

    context = {
        'last_part_status': last_part_status,
        'last_barcode': lm,
        'form': form,
        'running_count': running_count,
        'title': 'Barcode Scan',
        'active_part': current_part_id,
        'part_select_options': select_part_options,
    }

    return render(request, 'barcode_verify/dup_scan.html', context=context)
