# quality/views.py
from django.shortcuts import render, get_object_or_404, redirect
from .models import Feat
from .forms import FeatForm
from plant.models.setupfor_models import Part
from django.db import transaction  
from django.db.models import F
from django.http import JsonResponse


def index(request):
    return render(request, 'quality/index.html')

def scrap_form(request):
    return render(request, 'quality/scrap_form.html')



def scrap_form_management(request):
    # Get all parts, whether or not they have feats
    parts = Part.objects.all().prefetch_related('feat_set')
    return render(request, 'quality/scrap_form_management.html', {'parts': parts})



def feat_create(request):
    part_id = request.GET.get('part_id')  # Retrieve the part ID from the query parameters
    if request.method == 'POST':
        form = FeatForm(request.POST)
        if form.is_valid():
            with transaction.atomic():  # Ensure atomic transaction
                # Save the new feat without adjusting orders
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
            # Save the updated feat without adjusting orders
            form.save()
            return redirect('scrap_form_management')
    else:
        form = FeatForm(instance=feat)
    return render(request, 'quality/feat_form.html', {'form': form})

def feat_delete(request, pk):
    feat = get_object_or_404(Feat, pk=pk)

    if request.method == 'POST':
        # Simply delete the feat without adjusting the orders of remaining feats
        feat.delete()
        return redirect('scrap_form_management')
    
    return render(request, 'quality/feat_confirm_delete.html', {'feat': feat})


def feat_move_up(request, pk):
    feat = get_object_or_404(Feat, pk=pk)
    if feat.order > 1:
        with transaction.atomic():
            # Decrement the order of the feat just above
            Feat.objects.filter(part=feat.part, order=feat.order - 1).update(order=F('order') + 1)
            # Move this feat up
            feat.order -= 1
            feat.save()
    return JsonResponse({'success': True})


def feat_move_down(request, pk):
    feat = get_object_or_404(Feat, pk=pk)
    max_order = feat.part.feat_set.count()
    if feat.order < max_order:
        with transaction.atomic():
            # Increment the order of the feat just below
            Feat.objects.filter(part=feat.part, order=feat.order + 1).update(order=F('order') - 1)
            # Move this feat down
            feat.order += 1
            feat.save()
    return JsonResponse({'success': True})