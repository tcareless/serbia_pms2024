# plant/forms.py

from django import forms
from .models import Asset, Part, SetupFor

class SetupForForm(forms.ModelForm):
    class Meta:
        model = SetupFor
        fields = ['asset', 'part', 'since']
        widgets = {
            'since': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

class AssetForm(forms.ModelForm):
    class Meta:
        model = Asset
        fields = ['asset_number']

class PartForm(forms.ModelForm):
    class Meta:
        model = Part
        fields = ['part_number']
