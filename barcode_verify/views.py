from django.shortcuts import render

def index(request):
  context = {'test': True}
  return render(request, 'barcode_verify/index.html', context)
