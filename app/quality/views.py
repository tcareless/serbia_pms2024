from django.shortcuts import render


def index(request):
    return render(request, 'quality/index.html')



def scrap_form(request):
    return render(request, 'quality/scrap_form.html')
