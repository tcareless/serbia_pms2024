from django.shortcuts import render, redirect
from django.contrib import messages
from django.conf import settings
from .forms import ToolLifeDataForm

def tool_report_form(request):
    print("tool_report_form view called")
    
    if request.method == 'POST':
        print("Handling POST request")
        print(f"POST data: {request.POST}")
        
        form = ToolLifeDataForm(request.POST)
        if form.is_valid():
            print("Form is valid")
            form.save()
            messages.success(request, 'The tool report was successfully submitted.')
            return redirect('tool_report_form')
        else:
            print("Form is not valid")
            print("Form errors:", form.errors)
            for field, errors in form.errors.items():
                print(f"Field: {field}")
                for error in errors:
                    print(f"Error: {error}")
    else:
        print("Handling GET request")
        form = ToolLifeDataForm()

    # Debug available choices
    print("Machine choices:", ToolLifeDataForm().fields['machine'].choices)
    print("Operation choices:", ToolLifeDataForm().fields['operation'].choices)

    response = render(request, 'tooling/tool_report_form.html', {'form': form})
    response['Cross-Origin-Opener-Policy'] = 'same-origin'
    response['Cross-Origin-Embedder-Policy'] = 'require-corp'
    print("Added COOP and COEP headers to the response.")
    
    return response
