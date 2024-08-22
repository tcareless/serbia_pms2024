# quality/forms.py
from django import forms
from .models import Feat
from plant.models.setupfor_models import Part

class FeatForm(forms.ModelForm):
    part = forms.ModelChoiceField(queryset=Part.objects.all(), label="Part Number")

    class Meta:
        model = Feat
        fields = ['part', 'name', 'order', 'alarm']  # Include the alarm field
