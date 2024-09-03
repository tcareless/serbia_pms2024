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
    REASON_CHOICES = [
        ('a', 'Unsure, part scrapped'),
        ('b', 'One part scanned twice'),
        ('c', 'Duplicate found, part tagged and in QA'),
        ('other', 'Other')
    ]

    employee_id = forms.CharField(max_length=10, min_length=3, required=True)
    unlock_code = forms.CharField(max_length=3, required=True)
    reason = forms.ChoiceField(choices=REASON_CHOICES, widget=forms.RadioSelect, required=True)
    other_reason = forms.CharField(max_length=255, required=False)

    def clean(self):
        cleaned_data = super().clean()
        reason = cleaned_data.get('reason')
        other_reason = cleaned_data.get('other_reason')

        if reason == 'other' and not other_reason:
            self.add_error('other_reason', 'This field is required when "Other" is selected.')

        return cleaned_data



class DuplicateBatchUtilityForm(forms.Form):
    barcodes = forms.CharField(widget=forms.Textarea(), required=False)

    def clean_barcodes(self):
        data = self.cleaned_data['barcodes']
        return data
    

from .models import BarCodePUN

class SupervisorSetupForm(forms.Form):
    COUNT_CHOICES = [
        ('default', 'Default'),
        ('variable', 'Variable'),
        ('set', 'Set Number'),
    ]

    part_select = forms.ModelChoiceField(
        queryset=BarCodePUN.objects.filter(active=True).order_by('name'),
        required=False,
        empty_label="Any Part"
    )
    count_type = forms.ChoiceField(choices=COUNT_CHOICES, required=True, label="Count Type")
    count = forms.IntegerField(required=False, min_value=0, label="Count")
    tag = forms.CharField(required=False, max_length=50, label="Tag")

    def clean_count(self):
        count_type = self.cleaned_data.get('count_type')
        count = self.cleaned_data.get('count')

        if count_type == 'set' and (count is None or count == ''):
            raise forms.ValidationError("Please specify a count value when 'Set Number' is selected.")
        
        if count_type != 'set':
            count = None  # Only keep the count if it's a set number
        
        return count

