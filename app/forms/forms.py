from django import forms
from .models import Form, FormQuestion

from django import forms
from .models import Form, FormQuestion, FormType

# OIS FormType specific metadata and questions
class OISForm(forms.ModelForm):
    part_number = forms.CharField(
        max_length=255, 
        required=True, 
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    operation = forms.CharField(
        max_length=255, 
        required=True, 
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    part_name = forms.CharField(
        max_length=255, 
        required=True, 
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    year = forms.CharField(
        max_length=4, 
        required=True, 
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    mod_level = forms.CharField(
        max_length=255, 
        required=True, 
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    machine = forms.CharField(
        max_length=255, 
        required=True, 
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    mod_date = forms.DateField(
        required=True, 
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )

    class Meta:
        model = Form
        fields = ['name', 'part_number', 'operation', 'part_name', 'year', 'mod_level', 'machine', 'mod_date']  # No need to explicitly add 'form_type' here

    def save(self, commit=True):
        form = super().save(commit=False)
        # Manually set the form_type to OIS (since it's not included in the form)
        form_type = FormType.objects.get(name="OIS")
        form.form_type = form_type
        if commit:
            form.save()
        return form



class OISQuestionForm(forms.ModelForm):
    feature = forms.CharField(
        max_length=255, 
        required=True, 
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    special_characteristic = forms.CharField(
        max_length=255, 
        required=False, 
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    characteristic = forms.CharField(
        max_length=255, 
        required=True, 
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    specifications = forms.CharField(
        max_length=255, 
        required=True, 
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    sample_frequency = forms.CharField(
        max_length=255, 
        required=True, 
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    sample_size = forms.CharField(
        max_length=255, 
        required=True, 
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    done_by = forms.CharField(
        max_length=255, 
        required=True, 
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = FormQuestion
        fields = ['feature', 'special_characteristic', 'characteristic', 'specifications', 'sample_frequency', 'sample_size', 'done_by']

# Similarly, you can create other forms for other form types.
