# passwords/forms.py
from django import forms
from ..models.password_models import Password

class PasswordForm(forms.ModelForm):
    class Meta:
        model = Password
        fields = ['machine', 'label', 'username', 'password']
        widgets = {
            'password': forms.TextInput(attrs={'type': 'text'}),  
        }
