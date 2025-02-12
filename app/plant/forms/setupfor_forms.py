#forms/setupfor_forms.py
from django import forms
from ..models.setupfor_models import Asset, Tally_Part, SetupFor

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
        fields = ['asset_number', 'asset_name']  # Added asset_name field

class PartForm(forms.ModelForm):
    class Meta:
        model = Tally_Part
        fields = ['part_number', 'part_name']  # Added part_name field
