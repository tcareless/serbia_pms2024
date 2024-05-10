from django import forms
from .models import ToolLifeData

class ToolLifeDataForm(forms.ModelForm):
    class Meta:
        model = ToolLifeData
        fields = [
            'machine', 'operation', 'shift', 'operator', 'tool_type', 'tool_status', 'tool_issue', 'expected_tool_life', 'actual_tool_life', 'tool_serial_number', 'comments'
        ]
        widgets = {
            'comments': forms.Textarea(attrs={'rows': 4}),
        }