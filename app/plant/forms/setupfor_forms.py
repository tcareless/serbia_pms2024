from django import forms
from ..models.setupfor_models import Asset, Part, SetupFor
from datetime import datetime
import time
from django.utils import timezone  # Make sure this line is included at the top of your file


class SetupForForm(forms.ModelForm):
    since = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        input_formats=['%Y-%m-%dT%H:%M'],
        required=True,
        label='Since',
    )

    class Meta:
        model = SetupFor
        fields = ['asset', 'part', 'since']

    def clean_since(self):
        since_datetime = self.cleaned_data.get('since')
        if since_datetime is None:
            raise forms.ValidationError("Please enter a valid date and time.")

        # Ensure the datetime is timezone-aware
        if timezone.is_naive(since_datetime):
            since_datetime = timezone.make_aware(since_datetime, timezone.get_current_timezone())

        # Convert to UTC
        since_datetime_utc = since_datetime.astimezone(timezone.utc)

        # Convert datetime to Unix timestamp
        unix_timestamp = int(since_datetime_utc.timestamp())

        return unix_timestamp


class AssetForm(forms.ModelForm):
    class Meta:
        model = Asset
        fields = ['asset_number', 'asset_name']  # Added asset_name field

class PartForm(forms.ModelForm):
    class Meta:
        model = Part
        fields = ['part_number', 'part_name']  # Added part_name field
