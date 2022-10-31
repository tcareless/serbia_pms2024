from django import forms

class ShiftLineForm(forms.Form):
  CHOICES = (('value1', 'text1'),('value2', 'text2'),)
  field = forms.ChoiceField(choices=CHOICES)
  # barcode = forms.CharField(widget=forms.TextInput(attrs={'autofocus': 'autofocus'}), required=False)

  # def clean_barcode(self):
  #   data = self.cleaned_data['barcode']

  #   return data

