# plant/views.py
import json
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from .models import SetupFor, Asset, Part
from .forms import SetupForForm, AssetForm, PartForm

def display_setups(request):
    setups = SetupFor.objects.all().order_by('-id')
    assets = Asset.objects.all().order_by('asset_number')
    return render(request, 'plant/display_setups.html', {'setups': setups, 'assets': assets})

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

def display_assets(request):
    assets = Asset.objects.all().order_by('-id')
    return render(request, 'plant/display_assets.html', {'assets': assets})

def create_asset(request):
    if request.method == 'POST':
        form = AssetForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('display_assets')
    else:
        form = AssetForm()
    return render(request, 'plant/asset_form.html', {'form': form, 'title': 'Add New Asset'})

def edit_asset(request, id):
    asset = get_object_or_404(Asset, id=id)
    if request.method == 'POST':
        form = AssetForm(request.POST, instance=asset)
        if form.is_valid():
            form.save()
            return redirect('display_assets')
    else:
        form = AssetForm(instance=asset)
    return render(request, 'plant/asset_form.html', {'form': form, 'title': 'Edit Asset'})

def delete_asset(request, id):
    asset = get_object_or_404(Asset, id=id)
    if request.method == 'POST':
        asset.delete()
        return redirect('display_assets')
    return render(request, 'plant/delete_asset.html', {'asset': asset})

def display_parts(request):
    parts = Part.objects.all().order_by('-id')
    return render(request, 'plant/display_parts.html', {'parts': parts})

def create_part(request):
    if request.method == 'POST':
        form = PartForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('display_parts')
    else:
        form = PartForm()
    return render(request, 'plant/part_form.html', {'form': form, 'title': 'Add New Part'})

def edit_part(request, id):
    part = get_object_or_404(Part, id=id)
    if request.method == 'POST':
        form = PartForm(request.POST, instance=part)
        if form.is_valid():
            form.save()
            return redirect('display_parts')
    else:
        form = PartForm(instance=part)
    return render(request, 'plant/part_form.html', {'form': form, 'title': 'Edit Part'})

def delete_part(request, id):
    part = get_object_or_404(Part, id=id)
    if request.method == 'POST':
        part.delete()
        return redirect('display_parts')
    return render(request, 'plant/delete_part.html', {'part': part})

def timeline_data(request):
    start_time = request.GET.get('start')
    end_time = request.GET.get('end')
    asset_id = request.GET.get('asset')
    
    setups = SetupFor.objects.filter(
        since__gte=start_time,
        since__lte=end_time,
        asset_id=asset_id
    ).order_by('since')
    
    labels = [setup.since for setup in setups]
    values = [1 for _ in setups]
    
    data = {
        'labels': labels,
        'values': values,
    }
    
    return JsonResponse(data)