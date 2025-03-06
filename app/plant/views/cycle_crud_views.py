from django.shortcuts import render
from ..forms.cycle_crud_forms import AssetCycleTimeForm

def asset_cycle_times_page(request):
    if request.method == 'POST':
        form = AssetCycleTimeForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            print("Asset:", data['asset'])
            print("Part:", data['part'])
            print("Cycle Time:", data['cycle_time'])
            print("Date & Time:", data['datetime'])
    else:
        form = AssetCycleTimeForm()

    return render(request, 'asset_cycle_times.html', {'form': form})
