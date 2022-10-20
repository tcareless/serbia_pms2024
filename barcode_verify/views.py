import re

from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib import messages
from django.db import IntegrityError

from barcode_verify.forms import VerifyBarcodeForm
from barcode_verify.models import LaserMark, BarCodePUN


def input(request):
  print(f"request.Post={request.POST}")
  print(f"request.session.session_key={request.session.session_key}")
  print(dir(request.session))

  # get data from session
  running_count = int(request.session.get('RunningCount', '0'))
  last_part = request.session.get('LastPart', '0')

  # initalize current_part if no barcode submited
  current_part = last_part

  select_part_options = BarCodePUN.objects.all()  # *TODO BarCodePun.objects.fileter(active=True)

  if request.method == 'POST':

    if 'set_count' in request.POST:
      messages.add_message(request, messages.INFO, 'Count reset.')
      running_count = int(request.POST.get('count',0) or 0)

    if 'submit' in request.POST:
      form = VerifyBarcodeForm(request.POST)
      current_part = int(request.POST.get('part_select', '0'))

      # reset counter if part type changes
      if not current_part == last_part:
        running_count = 0

      if form.is_valid():

        #check the data here
        bar_code = form.cleaned_data.get('barcode')

        bar_code_PUN = BarCodePUN.objects.get(id=current_part)

        try:
          if re.search(bar_code_PUN.regex, bar_code):
            lm = LaserMark(bar_code=bar_code)
            lm.save()
          else:
            raise ValueError()

        # saving a duplicate barcode in the DB raises IntegrityError due to UNIQUE constraint
        except IntegrityError as e:
          messages.add_message(request, messages.ERROR, 'Duplicate Barcode Detected!')
          print('Duplicate: ', lm.scanned_at)

        except ValueError as e:
          messages.add_message(request, messages.ERROR, 'Invalid Barcode Format!')

        else:
          messages.add_message(request, messages.SUCCESS, 'Valid Barcode Scanned')
          running_count += 1
          print(running_count)

  # use the session to maintain a running count of parts per user
  request.session['RunningCount'] = running_count
  request.session['LastPart'] = current_part
  form = VerifyBarcodeForm()

  context = {
    'test': True,
    'form': form,
    'running_count': running_count,
    'title': 'Barcode Verify',
    'active_part': current_part,
    'part_select_options': select_part_options,
  }

  return render(request, 'barcode_verify/input.html', context=context)


