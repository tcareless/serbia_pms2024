from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect
from django.urls import reverse

from django.db import IntegrityError
from barcode_verify.forms import VerifyBarcodeForm
from barcode_verify.models import LaserMark

def input(request):
  print(request.POST)

  running_count = 0
  if request.method == 'POST':
    if 'reset_count' in request.POST:
      running_count = 0

    form = VerifyBarcodeForm(request.POST)
    if form.is_valid():

      if 'set_count' in request.POST:
        print(request.POST)
        running_count = int(request.POST.get('count',0))

      if 'submit' in request.POST:

        running_count = int(request.session.get('RunningCount', '0'))
        print(form.cleaned_data)
        #check the data here
        bar_code = form.cleaned_data.get('barcode')

        try:
            lm = LaserMark(bar_code=bar_code)
            lm.save()
        except IntegrityError as e:
            print('*** Duplicate Barcode ***')

        running_count += 1
        form = VerifyBarcodeForm()

  else:
    form = VerifyBarcodeForm()

  # use the session to maintain a running count of parts
  request.session['RunningCount'] = running_count

  context = {
    'test': True,
    'form': form,
    'running_count': running_count,
    'title': 'Barcode Verify',
    'part_number': '50-8670',
  }

  return render(request, 'barcode_verify/input.html', context=context)


