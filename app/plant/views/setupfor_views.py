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

from datetime import datetime, timedelta

def display_setups(request):
    # Calculate the date 30 days ago from today
    last_30_days_unix = int((timezone.now() - timedelta(days=30)).timestamp())
    current_unix = int(timezone.now().timestamp())

    # Parse date range from GET parameters
    from_date_unix = int(request.GET.get('from_date', last_30_days_unix))
    to_date_unix = int(request.GET.get('to_date', current_unix))

    # Filter by Unix timestamp range
    setups = SetupFor.objects.filter(since__range=[from_date_unix, to_date_unix]).order_by('-since')
    assets = Asset.objects.all().order_by('asset_number')
    part = None

    if request.method == 'POST':
        asset_number = request.POST.get('asset_number')
        timestamp_str = request.POST.get('timestamp')
        if asset_number and timestamp_str:
            try:
                # Parse the timestamp from ISO 8601 format
                timestamp = int(datetime.fromisoformat(timestamp_str).timestamp())
                part = SetupFor.setupfor_manager.get_part_at_time(asset_number, timestamp)
            except ValueError:
                part = None

    return render(request, 'setupfor/display_setups.html', {'setups': setups, 'assets': assets, 'part': part})



from django.shortcuts import render, redirect
from django.utils import timezone
from ..models.setupfor_models import SetupFor
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
            print("Form is valid.")
            setupfor = form.save()  # Save the instance directly since 'since' is now an integer
            print("SetupFor instance saved with id:", setupfor.id)
            return redirect('display_setups')
        else:
            print("Form is invalid. Errors:", form.errors)
    
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

def edit_setupfor(request, id):
    # Get the SetupFor object by id or return 404 if not found
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
            print("Form is valid.")
            form.save()  # Save the updated instance
            print("SetupFor instance updated with id:", setupfor.id)
            return redirect('display_setups')
        else:
            print("Form is invalid. Errors:", form.errors)
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

from django.http import JsonResponse

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
            # Convert the timestamp from a string to an integer
            if timestamp_unix:
                timestamp = int(timestamp_unix)  # Use Unix timestamp directly
            else:
                raise ValueError("Timestamp is required")

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
from django.views.decorators.csrf import csrf_exempt
from ..models.setupfor_models import SetupFor, Asset, Part
import json

@csrf_exempt
def update_part_for_asset(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST requests are allowed'}, status=405)

    try:
        data = json.loads(request.body)
        asset_number = data.get('asset_number')
        part_number = data.get('part_number')
        timestamp_unix = data.get('timestamp')

        if not (asset_number and part_number and timestamp_unix):
            return JsonResponse({'error': 'Missing asset_number, part_number, or timestamp'}, status=400)

        # Convert Unix timestamp to a datetime object
        timestamp = timezone.datetime.fromtimestamp(int(timestamp_unix))

        asset = Asset.objects.filter(asset_number=asset_number).first()
        part = Part.objects.filter(part_number=part_number).first()

        if not asset or not part:
            return JsonResponse({'error': 'Asset or part not found'}, status=404)

        # Check the most recent SetupFor record
        recent_setup = SetupFor.objects.filter(asset=asset).order_by('-since').first()
        if recent_setup and recent_setup.part == part:
            return JsonResponse({
                'message': 'No new changeover needed; the asset is already running this part',
                'asset_number': asset_number,
                'part_number': part_number,
                'since': recent_setup.since
            })

        # Create a new SetupFor record with the provided Unix timestamp
        new_setup = SetupFor.objects.create(asset=asset, part=part, since=int(timestamp_unix))
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
