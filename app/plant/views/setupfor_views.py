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
import time



def index(request):
    return render(request, 'setupfor/index.html')

def natural_sort_key(s):
    # Split the string into numeric and non-numeric parts
    parts = re.split(r'(\d+)', s)
    # Convert numeric parts to integers
    return [int(part) if part.isdigit() else part for part in parts]

from datetime import datetime, timedelta

import time
from django.utils import timezone
from django.shortcuts import render
from ..models.setupfor_models import SetupFor

def display_setups(request):
    # Calculate the date 30 days ago from today as a Unix timestamp
    last_30_days = int((timezone.now() - timezone.timedelta(days=30)).timestamp())
    
    # Get the date range from GET parameters if provided
    from_date_str = request.GET.get('from_date')
    to_date_str = request.GET.get('to_date')

    # Convert provided dates to Unix timestamps, or use the default 30-day range
    if from_date_str and to_date_str:
        try:
            from_date = int(time.mktime(timezone.datetime.fromisoformat(from_date_str).timetuple()))
            to_date = int(time.mktime(timezone.datetime.fromisoformat(to_date_str).timetuple()))
        except ValueError:
            from_date = last_30_days
            to_date = int(time.time())
    else:
        from_date = last_30_days
        to_date = int(time.time())

    # Filter SetupFor objects within the specified Unix timestamp range
    setups = SetupFor.objects.filter(since__range=[from_date, to_date]).order_by('-since')
    assets = Asset.objects.all().order_by('asset_number')
    part = None

    if request.method == 'POST':
        asset_number = request.POST.get('asset_number')
        timestamp_str = request.POST.get('timestamp')
        if asset_number and timestamp_str:
            try:
                timestamp = int(time.mktime(timezone.datetime.fromisoformat(timestamp).timetuple()))
                part = SetupFor.setupfor_manager.get_part_at_time(asset_number, timestamp)
            except ValueError:
                part = None

    return render(request, 'setupfor/display_setups.html', {'setups': setups, 'assets': assets, 'part': part})


from django.shortcuts import render, redirect
from ..forms.setupfor_forms import SetupForForm

def create_setupfor(request):
    if request.method == 'POST':
        post_data = request.POST.copy()  # Create a mutable copy of POST data
        
        # Extract and convert 'since' if present in the POST data
        since_str = post_data.get('since')
        if since_str:
            try:
                # Parse the datetime string to a Unix timestamp
                since_datetime = datetime.fromisoformat(since_str)
                post_data['since'] = int(since_datetime.timestamp())
                print("Converted 'since' to Unix timestamp:", post_data['since'])
            except ValueError:
                print("Invalid datetime format for 'since'")
        
        form = SetupForForm(post_data)
        
        if form.is_valid():
            setup = form.save()  # No need to modify `since` here since it's already a Unix timestamp
            return redirect('display_setups')
        else:
            print("Form errors:", form.errors)  # Debug statement for form errors
    else:
        form = SetupForForm()
        print("Rendering empty form for GET request.")

    return render(request, 'setupfor/setupfor_form.html', {
        'form': form,
        'title': 'Add New SetupFor'
    })


from datetime import datetime
from django.shortcuts import render, redirect, get_object_or_404
from ..models.setupfor_models import SetupFor
from ..forms.setupfor_forms import SetupForForm


from django.shortcuts import render, redirect, get_object_or_404
from ..forms.setupfor_forms import SetupForForm

def edit_setupfor(request, id):
    setupfor = get_object_or_404(SetupFor, id=id)

    if request.method == 'POST':
        post_data = request.POST.copy()  # Make a mutable copy of POST data

        # Convert 'since' to Unix timestamp if it's in datetime format
        since_str = post_data.get('since')
        if since_str:
            try:
                # Parse the datetime string into a Unix timestamp
                since_datetime = datetime.fromisoformat(since_str)
                post_data['since'] = int(since_datetime.timestamp())
                print("Converted 'since' to Unix timestamp:", post_data['since'])
            except ValueError:
                print("Invalid datetime format for 'since'")

        # Initialize the form with converted data
        form = SetupForForm(post_data, instance=setupfor)

        if form.is_valid():
            setup = form.save(commit=False)
            print("Updated 'since' value (Unix timestamp):", setup.since)  # Debug statement

            setup.save()  # Save without further conversion
            return redirect('display_setups')
        else:
            print("Form errors:", form.errors)  # Debug statement for form errors
    else:
        form = SetupForForm(instance=setupfor)
        print("Rendering form for editing existing SetupFor instance.")

    return render(request, 'setupfor/setupfor_form.html', {
        'form': form,
        'title': 'Edit SetupFor'
    })






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

from django.utils import timezone
from django.http import JsonResponse
import time

def fetch_part_for_asset(request):
    # Get asset number and timestamp from GET parameters
    asset_number = request.GET.get('asset_number')
    timestamp_unix = request.GET.get('timestamp')

    # Initialize the response data
    response_data = {
        'asset_number': asset_number,
        'timestamp': timestamp_unix,
        'part_number': None
    }

    if asset_number:
        try:
            # Use provided timestamp, or default to the current Unix timestamp
            if timestamp_unix:
                timestamp = int(timestamp_unix)
            else:
                # Default to current time in Unix timestamp format
                timestamp = int(time.time())
                response_data['timestamp'] = timestamp  # Update response to reflect the default timestamp

            # Fetch part using the timestamp as an integer
            part = SetupFor.setupfor_manager.get_part_at_time(asset_number, timestamp)
            
            # Update response data with the part number if found
            if part:
                response_data['part_number'] = part.part_number
            else:
                response_data['error'] = 'No part found for the given asset at the specified time.'
        
        except (ValueError, TypeError):
            # Handle invalid timestamp format
            response_data['error'] = 'Invalid timestamp format. Please use a valid Unix timestamp (e.g., 1693503600).'
    else:
        response_data['error'] = 'Missing asset_number parameter.'

    return JsonResponse(response_data)


# =======================================================================================
# Example usages of the fetch_part_for_asset API endpoint
# =======================================================================================
# To query the API endpoint, make a GET request with 'asset_number' as a required parameter 
# and 'timestamp' as an optional Unix timestamp (in seconds).
# 
# - 'asset_number' is required to identify the asset.
# - 'timestamp' is optional; if omitted, the API will default to the current Unix timestamp.
#   When provided, 'timestamp' should be an integer Unix timestamp (e.g., 1693503600).
#
# Example usage with curl:
# ---------------------------------------------------------------------------------------
# 1. Request with a specific timestamp (Unix timestamp in seconds):
# curl -X GET "http://10.4.1.232:8082/plant/api/fetch_part_for_asset/?asset_number=769&timestamp=1730313000"
#
# 2. Request without a timestamp (defaults to current time):
# curl -X GET "http://10.4.1.232:8082/plant/api/fetch_part_for_asset/?asset_number=769"
#
# =======================================================================================










# =============================================================================================
# =============================================================================================
# =============================== Input API Endpoint ==========================================
# =============================================================================================
# =============================================================================================


from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from ..models.setupfor_models import SetupFor, Asset, Part
import json
import time

@csrf_exempt
def update_part_for_asset(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST requests are allowed'}, status=405)

    try:
        data = json.loads(request.body)
        asset_number = data.get('asset_number')
        part_number = data.get('part_number')
        timestamp_unix = data.get('timestamp')

        if not (asset_number and part_number):
            return JsonResponse({'error': 'Missing asset_number or part_number'}, status=400)

        # Use provided timestamp, or default to the current Unix timestamp
        if timestamp_unix:
            timestamp = int(timestamp_unix)
        else:
            timestamp = int(time.time())
            timestamp_unix = timestamp  # Update the variable for consistent handling below

        # Convert Unix timestamp to a datetime object
        timestamp_dt = timezone.datetime.fromtimestamp(timestamp)

        asset = Asset.objects.filter(asset_number=asset_number).first()
        part = Part.objects.filter(part_number=part_number).first()

        if not asset or not part:
            return JsonResponse({'error': 'Asset or part not found'}, status=404)

        # Check if a recent SetupFor record exists with the same asset, part, and timestamp
        existing_setup = SetupFor.objects.filter(asset=asset, part=part, since=timestamp_unix).exists()
        if existing_setup:
            return JsonResponse({
                'message': 'No new changeover needed; the asset is already running this part with the same timestamp',
                'asset_number': asset_number,
                'part_number': part_number,
                'since': timestamp_unix
            })

        # Otherwise, create a new SetupFor record with the provided Unix timestamp
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




# =======================================================================================
# Example usage of the update_part_for_asset API endpoint
# =======================================================================================
# To update the part running on a specific asset, make a POST request to this endpoint
# with 'asset_number', 'part_number', and 'timestamp' provided in the JSON payload.
#
# - 'asset_number' is required to identify the asset to update.
# - 'part_number' specifies the new part to run on the asset.
# - 'timestamp' is optional; if omitted, the API will default to the current Unix timestamp.
#   When provided, 'timestamp' should be an integer Unix timestamp in seconds (e.g., 1693503600).
#
# The API will check if the specified part is already running on the asset:
# - If the asset is already running the specified part with the provided timestamp, 
#   it will return a message indicating that no new changeover is needed.
# - If the part is not currently running, it will create a new changeover record.
#
# Example usage with curl:
# ---------------------------------------------------------------------------------------
# 1. Request to set a part on an asset with a specific timestamp:
# curl -X POST "http://10.4.1.232:8082/plant/api/update_part_for_asset/" \
#      -H "Content-Type: application/json" \
#      -d '{
#            "asset_number": "1513",
#            "part_number": "50-5214",
#            "timestamp": 1730313000
#          }'
#
# 2. Request to set a part on an asset without a timestamp (defaults to current time):
# curl -X POST "http://10.4.1.232:8082/plant/api/update_part_for_asset/" \
#      -H "Content-Type: application/json" \
#      -d '{
#            "asset_number": "1513",
#            "part_number": "50-5214"
#          }'
#
# Expected Responses:
# ---------------------------------------------------------------------------------------
# - If the asset is already running the specified part with the same timestamp:
#   {
#       "message": "No new changeover needed; the asset is already running this part",
#       "asset_number": "1513",
#       "part_number": "50-5214",
#       "since": 1730313000
#   }
#
# - If the asset is not currently running the specified part:
#   {
#       "message": "New changeover created",
#       "asset_number": "1513",
#       "part_number": "50-5214",
#       "since": 1730313000
#   }
#
# =======================================================================================


