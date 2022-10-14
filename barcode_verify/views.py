from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect
from django.urls import reverse

from barcode_verify.forms import VerifyBarcodeForm

def input(request):

  running_count = 0
  if request.method == 'POST':
    form = VerifyBarcodeForm(request.POST)
    running_count = int(request.session.get('RunningCount', '0'))



    if form.is_valid():
      #check the data here

      running_count += 1

  else:
    form = VerifyBarcodeForm()

  # use the session to maintain a running count of parts
  request.session['RunningCount'] = running_count

  context = {
    'test': True,
    'form': form,
    'running_count': running_count,
  }

  return render(request, 'barcode_verify/input.html', context=context)


