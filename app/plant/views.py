# plant/views.py
import json
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from .models import SetupFor, Asset, Part
from .forms import SetupForForm, AssetForm, PartForm
from django.utils import timezone
import re

def natural_sort_key(s):
    # Split the string into numeric and non-numeric parts
    parts = re.split(r'(\d+)', s)
    # Convert numeric parts to integers
    return [int(part) if part.isdigit() else part for part in parts]

def display_setups(request):
    # Get all SetupFor objects ordered by 'since' in descending order
    setups = SetupFor.objects.all().order_by('-since')
    # Get all Asset objects ordered by 'asset_number'
    assets = Asset.objects.all().order_by('asset_number')
    part = None

    if request.method == 'POST':
        # Get asset number and timestamp from POST data
        asset_number = request.POST.get('asset_number')
        timestamp = request.POST.get('timestamp')
        if asset_number and timestamp:
            try:
                # Convert timestamp to datetime object
                timestamp = timezone.datetime.fromisoformat(timestamp)
                # Get the part at the given time for the asset
                part = SetupFor.setupfor_manager.get_part_at_time(asset_number, timestamp)
            except ValueError:
                # Handle invalid timestamp format
                part = None

    # Render the template with the setups, assets, and part
    return render(request, 'plant/display_setups.html', {'setups': setups, 'assets': assets, 'part': part})

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
    # Get the SetupFor object by id or return 404 if not found
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
    # Get the SetupFor object by id or return 404 if not found
    setupfor = get_object_or_404(SetupFor, id=id)
    if request.method == 'POST':
        setupfor.delete()
        return redirect('display_setups')
    return render(request, 'plant/delete_setupfor.html', {'setupfor': setupfor})

def display_assets(request):
    # Get all Asset objects and sort them naturally by 'asset_number'
    assets = list(Asset.objects.all())
    assets.sort(key=lambda a: natural_sort_key(a.asset_number))
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
    # Get the Asset object by id or return 404 if not found
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
    # Get the Asset object by id or return 404 if not found
    asset = get_object_or_404(Asset, id=id)
    if request.method == 'POST':
        asset.delete()
        return redirect('display_assets')
    return render(request, 'plant/delete_asset.html', {'asset': asset})

def display_parts(request):
    # Get all Part objects and sort them naturally by 'part_number'
    parts = list(Part.objects.all())
    parts.sort(key=lambda p: natural_sort_key(p.part_number))
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
    # Get the Part object by id or return 404 if not found
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
    # Get the Part object by id or return 404 if not found
    part = get_object_or_404(Part, id=id)
    if request.method == 'POST':
        part.delete()
        return redirect('display_parts')
    return render(request, 'plant/delete_part.html', {'part': part})
