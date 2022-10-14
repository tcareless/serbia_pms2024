from django import forms

class VerifyBarcodeForm(forms.Form):
  barcode = forms.CharField()

  def clean_barcode(self):
    data = self.cleaned_data['barcode']

    return data

