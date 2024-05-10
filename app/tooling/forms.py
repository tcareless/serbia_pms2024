from django import forms
from .models import ToolLifeData

class ToolLifeDataForm(forms.ModelForm):
    class Meta:
        # Specify the model to be used for the form
        model = ToolLifeData
        # Define the fields to be included in the form
        fields = [
            'machine', 'operation', 'shift', 'operator', 'tool_type', 'tool_status', 'tool_issue', 'expected_tool_life', 'actual_tool_life', 'tool_serial_number', 'comments'
        ]
        # Customize appearance of 'comments' field with a Textarea widget
        widgets = {
            'comments': forms.Textarea(attrs={'rows': 4}),
        }
