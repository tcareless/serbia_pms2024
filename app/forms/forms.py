from django import forms
from .models import FormQuestion

class QuestionForm(forms.ModelForm):
    feature = forms.CharField(max_length=255, required=True)
    characteristic = forms.CharField(max_length=255, required=True)
    specifications = forms.CharField(max_length=255, required=False)
    sample_frequency = forms.CharField(max_length=255, required=False)
    sample_size = forms.CharField(max_length=255, required=False)
    done_by = forms.CharField(max_length=255, required=False)

    class Meta:
        model = FormQuestion
        fields = ['form']  # Add fields related to form association if necessary
