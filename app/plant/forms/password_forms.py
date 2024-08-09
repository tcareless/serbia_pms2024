# passwords/forms.py
from django import forms
from ..models.password_models import Password
from ..models.setupfor_models import Asset  # Import the Asset model

class PasswordForm(forms.ModelForm):
    class Meta:
        model = Password
        fields = ['password_asset', 'label', 'username', 'password']  # Updated field name
        widgets = {
            'password_asset': forms.Select(),  # Dropdown for selecting the asset
            'password': forms.TextInput(attrs={'type': 'text'}),  
        }

