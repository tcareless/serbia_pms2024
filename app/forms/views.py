from django.shortcuts import render, get_object_or_404, redirect
from .models import FormType
from .forms import FormTypeForm

def index(request):
    return render(request, 'forms/index.html')

def form_type_list(request):
    form_types = FormType.objects.all()
    return render(request, 'forms/form_type_list.html', {'form_types': form_types})

def form_type_create(request):
    if request.method == 'POST':
        form = FormTypeForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('form_type_list')
    else:
        form = FormTypeForm()
    return render(request, 'forms/form_type_form.html', {'form': form})

def form_type_update(request, pk):
    form_type = get_object_or_404(FormType, pk=pk)
    if request.method == 'POST':
        form = FormTypeForm(request.POST, instance=form_type)
        if form.is_valid():
            form.save()
            return redirect('form_type_list')
    else:
        form = FormTypeForm(instance=form_type)
    return render(request, 'forms/form_type_form.html', {'form': form})

def form_type_delete(request, pk):
    form_type = get_object_or_404(FormType, pk=pk)
    if request.method == 'POST':
        form_type.delete()
        return redirect('form_type_list')
    return render(request, 'forms/form_type_confirm_delete.html', {'form_type': form_type})
