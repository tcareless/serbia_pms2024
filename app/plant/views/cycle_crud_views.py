from django.shortcuts import render
from django.http import HttpResponse
from ..models.setupfor_models import Asset, Part

def asset_cycle_times_page(request):
    if request.method == "POST":
        # Get submitted form data
        asset_id = request.POST.get('asset')
        part_id = request.POST.get('part')
        cycle_time = request.POST.get('cycle_time')
        effective_date = request.POST.get('effective_date')

        # Print the received form data
        print("\n==== Received Form Data ====")
        print(f"Asset ID: {asset_id}")
        print(f"Part ID: {part_id}")
        print(f"Cycle Time: {cycle_time}")
        print(f"Effective Date: {effective_date}\n")

        return HttpResponse("Form submitted successfully! Check the server logs.")

    # If GET, just load the form
    context = {
        'assets': Asset.objects.all(),
        'parts': Part.objects.all()
    }
    return render(request, 'asset_cycle_times.html', context)
