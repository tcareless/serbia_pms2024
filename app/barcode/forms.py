from django import forms
from django.utils import timezone
from django.utils import dateformat
from django.forms.widgets import DateInput
from django.forms.widgets import Select


class BarcodeScanForm(forms.Form):
    barcode = forms.CharField(widget=forms.TextInput(
        attrs={'autofocus': 'autofocus'}), required=False)

    def clean_barcode(self):
        data = self.cleaned_data['barcode']

        return data


class BatchBarcodeScanForm(forms.Form):
    barcodes = forms.CharField(widget=forms.Textarea(), required=False)

    def clean_barcode(self):
        data = self.cleaned_data['barcode']

        return data

class BarcodeQueryForm(forms.Form):
    barcode = forms.CharField(widget=forms.TextInput(attrs={'autofocus': 'autofocus'}))


ASSETS = [ ("1750", "1750"), ("1725", "1725"), ("1724", "1724"), ("1505", "1505"), ("1534", "1534"), ("1811", "1811") ]
class LaserQueryForm(forms.Form):
    start_date = forms.DateField(initial=dateformat.format(timezone.now(),'Y-m-d'), widget=DateInput(attrs={'type':'date'}))
    end_date = forms.DateField(initial=dateformat.format(timezone.now(),'Y-m-d'), widget=DateInput(attrs={'type':'date'}))
    asset = forms.ChoiceField(choices=ASSETS)
