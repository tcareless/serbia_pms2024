from django.shortcuts import render
from ..forms.cycle_crud_forms import AssetCycleTimeForm
from ..models.setupfor_models import AssetCycleTimes
import time
from datetime import datetime
import pytz  # For timezone conversion if needed

def asset_cycle_times_page(request):
    if request.method == 'POST':
        form = AssetCycleTimeForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            epoch_timestamp = int(data['datetime'].timestamp())  # Convert datetime to epoch

            # Save to AssetCycleTimes model
            AssetCycleTimes.objects.create(
                asset=data['asset'],
                part=data['part'],
                cycle_time=float(data['cycle_time']),
                effective_date=epoch_timestamp
            )

            print("Entry saved successfully!")

    else:
        form = AssetCycleTimeForm()

    # Fetch past entries and convert effective_date from epoch to datetime
    past_entries = AssetCycleTimes.objects.all().order_by('-created_at')
    
    for entry in past_entries:
        entry.effective_date_display = datetime.fromtimestamp(entry.effective_date, pytz.utc).strftime("%Y-%m-%d %H:%M")

    return render(request, 'asset_cycle_times.html', {'form': form, 'past_entries': past_entries})



def update_asset_cycle_times_page(request):

    print(f'{request}')

    return