from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import ToolLifeDataForm

# Create your views here.

def tool_report_form(request):
    if request.method == 'POST':
        # If it's a POST request, initialize the form with the POST data
        form = ToolLifeDataForm(request.POST)
        # Check if the form data is valid
        if form.is_valid():
            # If the form data is valid, save it to the database
            form.save()
            # Display a success message
            messages.success(request, 'The tool report was successfully submitted.')
            # Redirect back to the same form page to clear the form
            return redirect('tool_report_form')
    else:
        # If it's not a POST request, create a new empty form
        form = ToolLifeDataForm()

    # Render the form page with the form object
    return render(request, 'tooling/tool_report_form.html', {'form': form})

