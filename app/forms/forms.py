from django import forms
from .models import FormQuestion

class QuestionForm(forms.ModelForm):
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
        fields = ['form']  # Add fields related to form association if necessary
