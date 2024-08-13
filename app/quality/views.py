# quality/views.py
from django.shortcuts import render, get_object_or_404, redirect
from .models import Feat
from .forms import FeatForm
from plant.models.setupfor_models import Part

def index(request):
    return render(request, 'quality/index.html')

def scrap_form(request):
    return render(request, 'quality/scrap_form.html')



def scrap_form_management(request):
    # Filter out parts that have no feats associated with them
    parts = Part.objects.filter(feat_set__isnull=False).distinct().prefetch_related('feat_set')
    return render(request, 'quality/scrap_form_management.html', {'parts': parts})


def feat_create(request):
    part_id = request.GET.get('part_id')  # Retrieve the part ID from the query parameters
    if request.method == 'POST':
        form = FeatForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('scrap_form_management')
    else:
        if part_id:
            part = get_object_or_404(Part, id=part_id)
            # Calculate the next order number
            next_order = part.feat_set.count() + 1
            form = FeatForm(initial={'part': part, 'order': next_order})  # Pre-fill part and order
        else:
            form = FeatForm()
    
    return render(request, 'quality/feat_form.html', {'form': form})


def feat_update(request, pk):
    feat = get_object_or_404(Feat, pk=pk)
    if request.method == 'POST':
        form = FeatForm(request.POST, instance=feat)
        if form.is_valid():
            form.save()
            return redirect('scrap_form_management')
    else:
        form = FeatForm(instance=feat)
    return render(request, 'quality/feat_form.html', {'form': form})

def feat_delete(request, pk):
    feat = get_object_or_404(Feat, pk=pk)
    part = feat.part  # Get the associated part before deleting the feat
    order_to_delete = feat.order  # Store the order number to delete

    if request.method == 'POST':
        feat.delete()

        # Auto-decrement the order of remaining feats
        feats_to_update = Feat.objects.filter(part=part, order__gt=order_to_delete)
        for f in feats_to_update:
            f.order -= 1
            f.save()

        return redirect('scrap_form_management')
    
    return render(request, 'quality/feat_confirm_delete.html', {'feat': feat})

