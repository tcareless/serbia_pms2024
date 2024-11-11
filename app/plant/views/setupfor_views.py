# setupfor/views.py
import json
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from ..models.setupfor_models import SetupFor, Asset, Part
from ..forms.setupfor_forms import SetupForForm, AssetForm, PartForm
from django.utils import timezone
import re
from django.core.paginator import Paginator
from django.db import models
from django.urls import reverse




def index(request):
    return render(request, 'setupfor/index.html')

def natural_sort_key(s):
    # Split the string into numeric and non-numeric parts
    parts = re.split(r'(\d+)', s)
    # Convert numeric parts to integers
    return [int(part) if part.isdigit() else part for part in parts]

from datetime import timedelta

def display_setups(request):
    # Calculate the date 30 days ago from today
    last_30_days = timezone.now() - timedelta(days=30)
    
    # Get the date range from GET parameters if provided
    from_date_str = request.GET.get('from_date')
    to_date_str = request.GET.get('to_date')
    
    if from_date_str and to_date_str:
        try:
            from_date = timezone.datetime.fromisoformat(from_date_str)
            to_date = timezone.datetime.fromisoformat(to_date_str)
        except ValueError:
            from_date = last_30_days
            to_date = timezone.now()
    else:
        from_date = last_30_days
        to_date = timezone.now()

    # Get SetupFor objects within the specified date range, ordered by 'since' in descending order
    setups = SetupFor.objects.filter(since__range=[from_date, to_date]).order_by('-since')
    assets = Asset.objects.all().order_by('asset_number')
    part = None

    if request.method == 'POST':
        asset_number = request.POST.get('asset_number')
        timestamp = request.POST.get('timestamp')
        if asset_number and timestamp:
            try:
                timestamp = timezone.datetime.fromisoformat(timestamp)
                part = SetupFor.setupfor_manager.get_part_at_time(asset_number, timestamp)
            except ValueError:
                part = None

    return render(request, 'setupfor/display_setups.html', {'setups': setups, 'assets': assets, 'part': part})


def create_setupfor(request):

    if request.method == 'POST':
        form = SetupForForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('display_setups')
    else:
        form = SetupForForm()
    return render(request, 'setupfor/setupfor_form.html', {'form': form, 'title': 'Add New SetupFor'})

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
    return render(request, 'setupfor/setupfor_form.html', {'form': form, 'title': 'Edit SetupFor'})

def delete_setupfor(request, id):
    # Get the SetupFor object by id or return 404 if not found
    setupfor = get_object_or_404(SetupFor, id=id)
    if request.method == 'POST':
        setupfor.delete()
        return redirect('display_setups')
    return render(request, 'setupfor/delete_setupfor.html', {'setupfor': setupfor})

def display_assets(request):
    # Get the search query
    search_query = request.GET.get('q', '')

    # Filter assets based on the search query, allowing search by asset_number or asset_name
    assets = Asset.objects.filter(
        models.Q(asset_number__icontains=search_query) | models.Q(asset_name__icontains=search_query)
    )
    assets = list(assets)
    assets.sort(key=lambda a: natural_sort_key(a.asset_number))

    # Handle pagination
    items_per_page = request.GET.get('show', '10')  # Default to 10 items per page
    try:
        items_per_page = int(items_per_page)
    except ValueError:
        items_per_page = 10  # Fallback to 10 if conversion fails

    paginator = Paginator(assets, items_per_page)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'setupfor/display_assets.html', {'page_obj': page_obj, 'search_query': search_query})

def create_asset(request):
    # Check if the user is coming from the password_create page
    from_password_create = request.GET.get('from_password_create', 'false') == 'true'

    if request.method == 'POST':
        form = AssetForm(request.POST)
        if form.is_valid():
            asset = form.save()
            if from_password_create:
                # Redirect back to the password_create page if coming from there
                return redirect(reverse('password_create'))
            return redirect('display_assets')
        else:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'errors': form.errors,
                })
    else:
        form = AssetForm()

    return render(request, 'setupfor/asset_form.html', {'form': form, 'title': 'Add New Asset'})


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
    return render(request, 'setupfor/asset_form.html', {'form': form, 'title': 'Edit Asset'})

def delete_asset(request, id):
    # Get the Asset object by id or return 404 if not found
    asset = get_object_or_404(Asset, id=id)
    if request.method == 'POST':
        asset.delete()
        return redirect('display_assets')
    return render(request, 'setupfor/delete_asset.html', {'asset': asset})

def display_parts(request):
    # Get the search query
    search_query = request.GET.get('q', '')

    # Filter parts based on the search query, allowing search by part_number or part_name
    parts = Part.objects.filter(
        models.Q(part_number__icontains=search_query) | models.Q(part_name__icontains=search_query)
    )
    parts = list(parts)
    parts.sort(key=lambda p: natural_sort_key(p.part_number))

    # Handle pagination
    items_per_page = request.GET.get('show', '10')  # Default to 10 items per page
    try:
        items_per_page = int(items_per_page)
    except ValueError:
        items_per_page = 10  # Fallback to 10 if conversion fails

    paginator = Paginator(parts, items_per_page)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'setupfor/display_parts.html', {'page_obj': page_obj, 'search_query': search_query})

def create_part(request):
    if request.method == 'POST':
        form = PartForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('display_parts')
    else:
        form = PartForm()
    return render(request, 'setupfor/part_form.html', {'form': form, 'title': 'Add New Part'})

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
    return render(request, 'setupfor/part_form.html', {'form': form, 'title': 'Edit Part'})

def delete_part(request, id):
    # Get the Part object by id or return 404 if not found
    part = get_object_or_404(Part, id=id)
    if request.method == 'POST':
        part.delete()
        return redirect('display_parts')
    return render(request, 'setupfor/delete_part.html', {'part': part})





# =========================================================================
# =========================================================================
# ======================== JSON API Endpoint View =========================
# =========================================================================
# =========================================================================

def fetch_part_for_asset(request):
    # Get asset number and timestamp from GET parameters
    asset_number = request.GET.get('asset_number')
    timestamp_str = request.GET.get('timestamp')

    # Initialize the response data
    response_data = {
        'asset_number': asset_number,
        'timestamp': timestamp_str,
        'part_number': None
    }

    if asset_number and timestamp_str:
        try:
            # Convert timestamp string to datetime object
            timestamp = timezone.datetime.fromisoformat(timestamp_str)
            # Get the part at the given time for the asset
            part = SetupFor.setupfor_manager.get_part_at_time(asset_number, timestamp)
            # Update response data with the part number
            if part:
                response_data['part_number'] = part.part_number
            else:
                response_data['error'] = 'No part found for the given asset at the specified time.'
        except ValueError:
            # Handle invalid timestamp format
            response_data['error'] = 'Invalid timestamp format. Please use ISO format (YYYY-MM-DDTHH:MM:SS).'
    else:
        response_data['error'] = 'Missing asset_number or timestamp parameter.'

    return JsonResponse(response_data)


# =======================================================================================
# Example usages of the fetch_part_for_asset API endpoint
# =======================================================================================
# To query the API endpoint, you need to make a GET request with 'asset_number' and 'timestamp' parameters.
# Below are some example usage using curl. The timestamp parameter should be a string representing the date and time in ISO 8601 format.: YYYY-MM-DDTHH:MM

# YYYY: Four-digit year (e.g., 2024)
# MM: Two-digit month (01 for January, 12 for December)
# DD: Two-digit day of the month (01 to 31)
# T: Separator between date and time (literally the letter 'T')
# HH: Two-digit hour in 24-hour format (00 to 23)
# MM: Two-digit minutes (00 to 59)

# Using curl:
# ---------------------------------------------------------------------------------------
# curl -X GET "http://10.4.1.232:8081/api/fetch_part_for_asset/?asset_number=Asset123&timestamp=2024-07-25T14:30:00"

# =======================================================================================









# =============================================================================================
# =============================================================================================
# =============================== Input API Endpoint ==========================================
# =============================================================================================
# =============================================================================================


from django.http import JsonResponse
from django.utils import timezone
from ..models.setupfor_models import SetupFor, Asset, Part
import json
from django.views.decorators.csrf import csrf_exempt


@csrf_exempt
def update_part_for_asset(request):
    # Ensure the request is a POST
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST requests are allowed'}, status=405)

    try:
        # Parse JSON data from request body
        data = json.loads(request.body)
        asset_number = data.get('asset_number')
        part_number = data.get('part_number')
        timestamp_str = data.get('timestamp')
        
        # Validate presence of required fields
        if not (asset_number and part_number and timestamp_str):
            return JsonResponse({'error': 'Missing asset_number, part_number, or timestamp'}, status=400)

        # Convert timestamp string to datetime
        try:
            timestamp = timezone.datetime.fromisoformat(timestamp_str)
        except ValueError:
            return JsonResponse({'error': 'Invalid timestamp format. Use ISO 8601 (YYYY-MM-DDTHH:MM:SS)'}, status=400)

        # Retrieve the Asset and Part instances
        asset = Asset.objects.filter(asset_number=asset_number).first()
        part = Part.objects.filter(part_number=part_number).first()

        # Ensure asset and part exist
        if not asset or not part:
            return JsonResponse({'error': 'Asset or part not found'}, status=404)

        # Check the most recent setup for this asset
        recent_setup = SetupFor.objects.filter(asset=asset).order_by('-since').first()

        # If there's a recent setup and it already has the same part, no new changeover is needed
        if recent_setup and recent_setup.part == part:
            return JsonResponse({
                'message': 'No new changeover needed; the asset is already running this part',
                'asset_number': asset_number,
                'part_number': part_number,
                'since': recent_setup.since
            })

        # Otherwise, create a new SetupFor record
        new_setup = SetupFor.objects.create(asset=asset, part=part, since=timestamp)
        return JsonResponse({
            'message': 'New changeover created',
            'asset_number': asset_number,
            'part_number': part_number,
            'since': new_setup.since
        })

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
