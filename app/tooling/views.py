from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import ToolLifeDataForm

def tool_report_form(request):
    if request.method == 'POST':
        form = ToolLifeDataForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('tooling:tool_report_form')
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

    response = render(request, 'tooling/tool_report_form.html', {'form': form})
    
    return response
