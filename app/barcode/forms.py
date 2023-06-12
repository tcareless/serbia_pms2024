from django import forms


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
