from django import forms

class VerifyBarcodeForm(forms.Form):
  barcode = forms.CharField(widget=forms.TextInput(attrs={'autofocus': 'autofocus'}), required=False)
#  barcode.widget.attrs.update(size='50')
#  barcode.widget.attrs.update({'class': 'form-control'})



  def clean_barcode(self):
    data = self.cleaned_data['barcode']

    return data

