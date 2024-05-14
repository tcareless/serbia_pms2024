from django.shortcuts import render, redirect
from django.contrib import messages
from django.conf import settings
from .forms import ToolLifeDataForm
import os

# Create your views here.

def tool_report_form(request):
    print("tool_report_form view called")
    
    if request.method == 'POST':
        print("Handling POST request")
        # If it's a POST request, initialize the form with the POST data
        form = ToolLifeDataForm(request.POST)
        # Check if the form data is valid
        if form.is_valid():
            print("Form is valid")
            # If the form data is valid, save it to the database
            form.save()
            # Display a success message
            messages.success(request, 'The tool report was successfully submitted.')
            # Redirect back to the same form page to clear the form
            return redirect('tool_report_form')
        else:
            print("Form is not valid")
            print(form.errors)
    else:
        print("Handling GET request")
        # If it's not a POST request, create a new empty form
        form = ToolLifeDataForm()

    # Log the static file paths
    static_css_path = settings.STATIC_URL + 'tooling/css/tool_report.css'
    static_js_path = settings.STATIC_URL + 'tooling/js/tool_report.js'
    print(f'Serving CSS from: {static_css_path}')
    print(f'Serving JS from: {static_js_path}')
    
    # Check if the files exist in the collected static directory
    css_file_path = os.path.join(settings.STATIC_ROOT, 'tooling/css/tool_report.css')
    js_file_path = os.path.join(settings.STATIC_ROOT, 'tooling/js/tool_report.js')
    css_file_exists = os.path.exists(css_file_path)
    js_file_exists = os.path.exists(js_file_path)
    print(f'CSS file exists in STATIC_ROOT: {css_file_exists} at {css_file_path}')
    print(f'JS file exists in STATIC_ROOT: {js_file_exists} at {js_file_path}')
    
    # Render the form page with the form object
    return render(request, 'tooling/tool_report_form.html', {'form': form})
