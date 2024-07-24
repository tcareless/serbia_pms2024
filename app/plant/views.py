# plant/views.py

from django.shortcuts import render, redirect, get_object_or_404
from .models import SetupFor, Asset, Part
from .forms import SetupForForm, AssetForm, PartForm

def display_setups(request):
    setups = SetupFor.objects.all()
    return render(request, 'plant/display_setups.html', {'setups': setups})

def create_setupfor(request):
    if request.method == 'POST':
        form = SetupForForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('display_setups')
    else:
        form = SetupForForm()
    return render(request, 'plant/setupfor_form.html', {'form': form, 'title': 'Add New SetupFor'})

def edit_setupfor(request, id):
    setupfor = get_object_or_404(SetupFor, id=id)
    if request.method == 'POST':
        form = SetupForForm(request.POST, instance=setupfor)
        if form.is_valid():
            form.save()
            return redirect('display_setups')
    else:
        form = SetupForForm(instance=setupfor)
    return render(request, 'plant/setupfor_form.html', {'form': form, 'title': 'Edit SetupFor'})

def delete_setupfor(request, id):
    setupfor = get_object_or_404(SetupFor, id=id)
    if request.method == 'POST':
        setupfor.delete()
        return redirect('display_setups')
    return render(request, 'plant/delete_setupfor.html', {'setupfor': setupfor})

def create_asset(request):
    if request.method == 'POST':
        form = AssetForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('create_setupfor')
    else:
        form = AssetForm()
    return render(request, 'plant/asset_form.html', {'form': form, 'title': 'Add New Asset'})

def create_part(request):
    if request.method == 'POST':
        form = PartForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('create_setupfor')
    else:
        form = PartForm()
    return render(request, 'plant/part_form.html', {'form': form, 'title': 'Add New Part'})
