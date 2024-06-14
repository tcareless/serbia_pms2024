from django import forms

class BarcodeScanForm(forms.Form):
    barcode = forms.CharField(widget=forms.TextInput(attrs={'autofocus': 'autofocus'}), required=False)

    def clean_barcode(self):
        data = self.cleaned_data['barcode']
        return data

class BatchBarcodeScanForm(forms.Form):
    barcodes = forms.CharField(widget=forms.Textarea(), required=False)

    def clean_barcodes(self):
        data = self.cleaned_data['barcodes']
        return data

class UnlockCodeForm(forms.Form):
    employee_id = forms.CharField(max_length=10, min_length=3, required=True)
    unlock_code = forms.CharField(max_length=3, required=True)
    comment = forms.CharField(widget=forms.Textarea, required=True)

    def clean_employee_id(self):
        data = self.cleaned_data['employee_id']
        return data

    def clean_unlock_code(self):
        data = self.cleaned_data['unlock_code']
        return data

    def clean_comment(self):
        data = self.cleaned_data['comment']
        return data
