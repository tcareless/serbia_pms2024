from django import forms
from bootstrap_datepicker_plus.widgets import DatePickerInput


class LasermarkSearchForm(forms.Form):
    asset_number = forms.CharField(max_length=30)
    time_start = forms.DateTimeField(widget=DatePickerInput())
    time_end = forms.DateTimeField(widget=DatePickerInput())


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
