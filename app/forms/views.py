from django.shortcuts import render, get_object_or_404, redirect
from .forms import FormTypeForm
from django.utils import timezone
import json
from .models import FormSubmission, FormType
from django.utils import timezone

def index(request):
    return render(request, 'forms/index.html')

def form_type_list(request):
    form_types = FormType.objects.all()
    return render(request, 'forms/form_types/form_type_list.html', {'form_types': form_types})

def form_type_create(request):
    if request.method == 'POST':
        form = FormTypeForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('form_type_list')
    else:
        form = FormTypeForm()
    return render(request, 'forms/form_types/form_type_form.html', {'form': form})

def form_type_update(request, pk):
    form_type = get_object_or_404(FormType, pk=pk)
    if request.method == 'POST':
        form = FormTypeForm(request.POST, instance=form_type)
        if form.is_valid():
            form.save()
            return redirect('form_type_list')
    else:
        form = FormTypeForm(instance=form_type)
    return render(request, 'forms/form_types/form_type_form.html', {'form': form})

def form_type_delete(request, pk):
    form_type = get_object_or_404(FormType, pk=pk)
    if request.method == 'POST':
        form_type.delete()
        return redirect('form_type_list')
    return render(request, 'forms/form_types/form_type_confirm_delete.html', {'form_type': form_type})

def tool_life_form(request):
    if request.method == 'POST':
        form_type = FormType.objects.get(name='Tool Life Forms')  # Use the existing FormType
        payload = {
            'tool_type': request.POST.get('tool_type'),
            'tool_condition': request.POST.get('tool_condition'),
            'tool_life_hours': request.POST.get('tool_life_hours'),
            'tool_notes': request.POST.get('tool_notes')
        }
        FormSubmission.objects.create(
            payload=payload,
            form_type=form_type,
            created_at=timezone.now()
        )
    return render(request, 'forms/tool_life_form.html')



from django.shortcuts import render, redirect
from .models import FormSubmission, FormType
from django.utils import timezone

def inspection_tally_sheet(request):
    if request.method == 'POST':
        form_type = FormType.objects.get(name='100% Inspection Tally Sheet')  # Use the existing FormType
        payload = {
            'inspector_name': request.POST.get('inspector_name'),
            'inspection_date': request.POST.get('inspection_date'),
            'units_inspected': request.POST.get('units_inspected'),
            'units_passed': request.POST.get('units_passed')
        }
        FormSubmission.objects.create(
            payload=payload,
            form_type=form_type,
            created_at=timezone.now()
        )
    return render(request, 'forms/inspection_tally_sheet.html')  # Use the template name associated with the FormType


