from django import forms
from ..models.setupfor_models import Asset, Part, SetupFor
from datetime import datetime
import time

class SetupForForm(forms.ModelForm):
    class Meta:
        model = SetupFor
        fields = ['asset', 'part', 'since']
        widgets = {
            'since': forms.NumberInput(attrs={'placeholder': 'Enter Unix timestamp (e.g., 1672531199)'}),
        }

    def clean_since(self):
        since = self.cleaned_data.get('since')
        
        # Ensure `since` is an integer representing a Unix timestamp
        if not isinstance(since, int):
            raise forms.ValidationError("Please enter a valid Unix timestamp as a whole number.")
        
        return since


class AssetForm(forms.ModelForm):
    class Meta:
        model = Asset
        fields = ['asset_number', 'asset_name']  # Added asset_name field

class PartForm(forms.ModelForm):
    class Meta:
        model = Part
        fields = ['part_number', 'part_name']  # Added part_name field
