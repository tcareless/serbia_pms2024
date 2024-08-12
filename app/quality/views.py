from django.shortcuts import render

def scrap_form(request):
    return render(request, 'quality/scrap_form.html')
