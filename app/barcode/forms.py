from django import forms

class BarcodeScanForm(forms.Form):
  barcode = forms.CharField(widget=forms.Textarea(), required=False)

  def clean_barcode(self):
    data = self.cleaned_data['barcode']

    return data