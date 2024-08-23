from django import forms
from .models import FormType

class FormTypeForm(forms.ModelForm):
    class Meta:
        model = FormType
        fields = ['name', 'template_name']
