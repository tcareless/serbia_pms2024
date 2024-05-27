"""
forms.py

The forms defined here allow for the creation and validation of ToolLifeData instances,
which are used to track various aspects of tool usage and performance in a manufacturing context.
"""

from django import forms
from .models import ToolLifeData

class ToolLifeDataForm(forms.ModelForm):
    """
    ToolLifeDataForm is a ModelForm for the ToolLifeData model. It provides fields for 
    capturing tool usage data such as machine, operation, shift, operator, tool type, 
    tool status, tool issue, expected tool life, actual tool life, tool serial number, and comments.
    """

    class Meta:
        model = ToolLifeData
        fields = [
            'machine', 'operation', 'shift', 'operator', 'tool_type', 'tool_status', 
            'tool_issue', 'expected_tool_life', 'actual_tool_life', 'tool_serial_number', 
            'comments'
        ]
        widgets = {
            'comments': forms.Textarea(attrs={'rows': 2}),
            'machine': forms.Select(),  # Use Select widget for dropdown
            'operation': forms.Select(),  # Use Select widget for dropdown
            'shift': forms.Select(),  # Use Select widget for dropdown
            'tool_type': forms.Select(),  # Use Select widget for dropdown
            'tool_status': forms.Select(), # Use Select Widget for dropdown
            'tool_issue': forms.Select(),  # Use Select widget for dropdown
        }

    def __init__(self, *args, **kwargs):
        """
        Initialize the ToolLifeDataForm with default values for select fields.
        
        Args:
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.
        """
        super(ToolLifeDataForm, self).__init__(*args, **kwargs)

        # Set initial choices for select fields with a default empty choice
        self.fields['machine'].choices = [('', '---------')] + ToolLifeData.MACHINE_NUMBER_CHOICES
        self.fields['operation'].choices = ToolLifeData.OPERATION_CHOICES
        self.fields['shift'].choices = [('', '---------')] + ToolLifeData.SHIFT_CHOICES
        self.fields['tool_type'].choices = [('', '---------')] + ToolLifeData.TOOL_TYPE_CHOICES
        self.fields['tool_issue'].choices = [('', '---------')] + ToolLifeData.TOOL_ISSUE_CHOICES
        self.fields['comments'].required = False
        self.fields['tool_serial_number'].required = False  # tool serial number optional





    
    def clean(self):
        """
        Clean the entire form and apply any additional validation needed.

        Returns:
            dict: Cleaned data.
        """
        cleaned_data = super(ToolLifeDataForm, self).clean()
        return cleaned_data
