from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .forms import ToolLifeDataForm
from .models import ToolLifeData

def tool_report_form(request):
    """
    Handle the submission and display of the tool report form.

    If the request method is POST, validate and process the submitted form data.
    If the form is valid, save the data, display a success message, store the form data ID in the session, and redirect to the label page.
    If the form is invalid, display an error message.
    If the request method is not POST, display an empty form.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: The HTTP response object with the rendered tool report form template.
    """
    if request.method == 'POST':
        form = ToolLifeDataForm(request.POST)  # Populate form with POST data
        if form.is_valid():  # Check if the form is valid
            tool_life_data = form.save()  # Save the form data to the database
            messages.success(request, 'Form submitted successfully!')
            request.session['form_data_id'] = tool_life_data.id  # Store the form data ID in the session
            return redirect('tooling:label_page')  # Redirect to the label page
        else:
            messages.error(request, 'Form submission failed. Please correct the errors and try again.')
    else:
        form = ToolLifeDataForm()  # Instantiate an empty form for GET request

    last_10_entries = ToolLifeData.objects.order_by('-created_at')[:10]  # Retrieve the last 10 entries from database

    return render(request, 'tooling/tool_report_form.html', {'form': form, 'last_10_entries': last_10_entries})

def label_page(request):
    """
    Display the label page with tool life data.

    Retrieve the tool life data based on the entry_id parameter from the GET request or from the session.
    If the entry_id is provided in the GET request, fetch the corresponding tool life data.
    If the entry_id is not provided, retrieve the tool life data ID from the session and fetch the corresponding data.
    If no data is found, raise a 404 error.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: The HTTP response object with the rendered label template.
    """
    entry_id = request.GET.get('entry_id')  # Get the entry_id from the GET request
    tool_life_data = None
    if entry_id:
        tool_life_data = get_object_or_404(ToolLifeData, id=entry_id)  # Fetch the tool life data based on entry_id
    else:
        tool_life_data_id = request.session.get('form_data_id', None)  # Retrieve the form data ID from the session
        if tool_life_data_id:
            tool_life_data = get_object_or_404(ToolLifeData, id=tool_life_data_id)  # Fetch the tool life data based on session ID

    return render(request, 'tooling/label.html', {'tool_life_data': tool_life_data})