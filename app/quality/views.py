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
    parts = Part.objects.all().prefetch_related('feat_set')
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
            form = FeatForm(initial={'part': part})  # Pre-fill the form with the part
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
    if request.method == 'POST':
        feat.delete()
        return redirect('scrap_form_management')
    return render(request, 'quality/feat_confirm_delete.html', {'feat': feat})
