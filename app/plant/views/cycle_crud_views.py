from django.shortcuts import render
from ..forms.cycle_crud_forms import AssetCycleTimeForm
import time


def asset_cycle_times_page(request):
    if request.method == 'POST':
        form = AssetCycleTimeForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            epoch_timestamp = int(data['datetime'].timestamp())  # Convert to epoch

            print("Asset:", data['asset'])
            print("Part:", data['part'])
            print("Cycle Time:", data['cycle_time'])
            print("Effective Date (Epoch Timestamp):", epoch_timestamp)  # Print epoch timestamp

    else:
        form = AssetCycleTimeForm()

    return render(request, 'asset_cycle_times.html', {'form': form})

