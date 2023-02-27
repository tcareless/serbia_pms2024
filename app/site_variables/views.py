from django.shortcuts import render

# relative import of forms
from .models import SiteVariableModel
from .forms import SiteVariableForm

# Create your views here.
from django.http import HttpResponse
def index(request):
    return HttpResponse("Hello, world. You're at the variables index.")

def create_view(request):
    # dictionary for initial data with
    # field names as keys
    context ={}
 
    # add the dictionary during initialization
    form = SiteVariableForm(request.POST or None)
    if form.is_valid():
        form.save()
         
    context['form']= form
    return render(request, "site_variables/create_view.html", context)