from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from ..models.setupfor_models import AssetCycleTimes, Asset, Part
import datetime
import time

BATCH_SIZE = 100

def asset_cycle_times_page(request):
    """
    Render the page with the first 100 AssetCycleTimes entries,
    plus lists of Assets and Parts for the dropdowns.
    """
    entries = AssetCycleTimes.objects.order_by('-created_at')[:BATCH_SIZE]
    total_count = AssetCycleTimes.objects.count()
    context = {
        'entries': entries,
        'assets': Asset.objects.all(),
        'parts': Part.objects.all(),
        'show_load_more': total_count > BATCH_SIZE
    }
    return render(request, 'asset_cycle_times.html', context)


@require_POST
def add_asset_cycle_time(request):
    """
    Handle AJAX POST to add a new asset cycle time entry.
    Expects:
      - asset (id)
      - part (id)
      - cycle_time (a number, as a string)
      - effective_date (a date string, e.g. '2025-03-06')
    Converts effective_date to an epoch timestamp.
    """
    try:
        asset_id = request.POST.get('asset')
        part_id = request.POST.get('part')
        cycle_time = float(request.POST.get('cycle_time'))
        effective_date_str = request.POST.get('effective_date')
        
        # Convert effective date string to epoch (assuming 'YYYY-MM-DD' format)
        effective_dt = datetime.datetime.strptime(effective_date_str, '%Y-%m-%d')
        epoch_effective = int(time.mktime(effective_dt.timetuple()))
        
        asset = get_object_or_404(Asset, pk=asset_id)
        part = get_object_or_404(Part, pk=part_id)
        
        new_entry = AssetCycleTimes.objects.create(
            asset=asset,
            part=part,
            cycle_time=int(cycle_time),  # stored as int per model definition
            effective_date=epoch_effective
        )
        
        # Render an HTML snippet for the new table row.
        row_html = f"""
        <tr data-id="{new_entry.id}">
            <td>{new_entry.id}</td>
            <td>{new_entry.asset.asset_number}</td>
            <td>{new_entry.part.part_number}</td>
            <td class="cycle-time">{new_entry.cycle_time}</td>
            <td class="effective-date">{new_entry.effective_date}</td>
            <td>{new_entry.created_at.strftime("%Y-%m-%d %H:%M:%S")}</td>
            <td>
                <button class="btn btn-sm btn-secondary edit-entry">Edit</button>
            </td>
        </tr>
        """
        return JsonResponse({'success': True, 'html': row_html})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@require_POST
def update_asset_cycle_time(request):
    """
    Handle AJAX POST to update an existing asset cycle time entry.
    Expects:
      - id (entry id)
      - cycle_time (a number)
      - effective_date (a date string in 'YYYY-MM-DD' format)
    """
    try:
        entry_id = request.POST.get('id')
        new_cycle_time = float(request.POST.get('cycle_time'))
        effective_date_str = request.POST.get('effective_date')
        
        effective_dt = datetime.datetime.strptime(effective_date_str, '%Y-%m-%d')
        epoch_effective = int(time.mktime(effective_dt.timetuple()))
        
        entry = get_object_or_404(AssetCycleTimes, pk=entry_id)
        entry.cycle_time = int(new_cycle_time)
        entry.effective_date = epoch_effective
        entry.save()
        
        # Return updated values for display
        # (If you need to reformat the epoch date to a readable form, you could do that here.)
        return JsonResponse({
            'success': True,
            'updated_cycle_time': entry.cycle_time,
            'updated_effective_date': entry.effective_date
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


def load_more_asset_cycle_times(request):
    """
    Load the next batch of asset cycle time entries.
    Expects a GET parameter 'offset' which indicates the number of rows already loaded.
    """
    try:
        offset = int(request.GET.get('offset', 0))
        next_entries = AssetCycleTimes.objects.order_by('-created_at')[offset:offset+BATCH_SIZE]
        total_count = AssetCycleTimes.objects.count()
        has_more = (offset + len(next_entries)) < total_count
        
        html_rows = ""
        for entry in next_entries:
            html_rows += f"""
            <tr data-id="{entry.id}">
                <td>{entry.id}</td>
                <td>{entry.asset.asset_number}</td>
                <td>{entry.part.part_number}</td>
                <td class="cycle-time">{entry.cycle_time}</td>
                <td class="effective-date">{entry.effective_date}</td>
                <td>{entry.created_at.strftime("%Y-%m-%d %H:%M:%S")}</td>
                <td>
                    <button class="btn btn-sm btn-secondary edit-entry">Edit</button>
                </td>
            </tr>
            """
        return JsonResponse({'success': True, 'html': html_rows, 'has_more': has_more})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)
