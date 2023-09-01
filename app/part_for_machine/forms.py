from django import forms
from django.forms.widgets import DateTimeInput

class PartForMachineDate(forms.Form):
    page_datetime = forms.DateTimeField(widget = DateTimeInput(
            attrs={
                'class': '',
                'type': 'datetime-local',
                'step': 'any',
            }
        ))

class PartForMachineEventForm(forms.Form):
    line = forms.CharField(widget=forms.HiddenInput())
    asset = forms.CharField(widget=forms.HiddenInput())
    part = forms.CharField()
    datetime = forms.DateTimeField(widget=forms.HiddenInput())
