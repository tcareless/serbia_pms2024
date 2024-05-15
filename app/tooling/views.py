from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import ToolLifeDataForm
import time

def tool_report_form(request):
    if request.method == 'POST':
        form = ToolLifeDataForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Form submitted successfully!')
            time.sleep(1)  # Pause for 1 second
            return redirect('tooling:label_page')
        else:
            messages.error(request, 'Form submission failed. Please correct the errors and try again.')
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = ToolLifeDataForm()

    return render(request, 'tooling/tool_report_form.html', {'form': form})

def label_page(request):
    return render(request, 'tooling/label.html')
