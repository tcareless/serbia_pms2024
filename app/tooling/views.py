from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .forms import ToolLifeDataForm
from .models import ToolLifeData

def tool_report_form(request):
    if request.method == 'POST':
        form = ToolLifeDataForm(request.POST)
        if form.is_valid():
            tool_life_data = form.save()
            messages.success(request, 'Form submitted successfully!')
            request.session['form_data_id'] = tool_life_data.id
            return redirect('tooling:label_page')
        else:
            messages.error(request, 'Form submission failed. Please correct the errors and try again.')
    else:
        form = ToolLifeDataForm()

    last_10_entries = ToolLifeData.objects.order_by('-created_at')[:10]

    return render(request, 'tooling/tool_report_form.html', {'form': form, 'last_10_entries': last_10_entries})

def label_page(request):
    entry_id = request.GET.get('entry_id')
    tool_life_data = None
    if entry_id:
        tool_life_data = get_object_or_404(ToolLifeData, id=entry_id)
    else:
        tool_life_data_id = request.session.get('form_data_id', None)
        if tool_life_data_id:
            tool_life_data = get_object_or_404(ToolLifeData, id=tool_life_data_id)
    return render(request, 'tooling/label.html', {'tool_life_data': tool_life_data, 'messages': messages.get_messages(request)})
