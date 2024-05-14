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
        self.fields['operation'].choices = [('', '---------')] + ToolLifeData.OPERATION_CHOICES
        self.fields['shift'].choices = [('', '---------')] + ToolLifeData.SHIFT_CHOICES
        self.fields['tool_type'].choices = [('', '---------')] + ToolLifeData.TOOL_TYPE_CHOICES
        self.fields['tool_issue'].choices = [('', '---------')] + ToolLifeData.TOOL_ISSUE_CHOICES

    def clean_machine(self):
        """
        Validate the machine field to ensure it is a valid choice.

        Returns:
            int: Validated machine number.

        Raises:
            forms.ValidationError: If the machine number is invalid.
        """
        machine = self.cleaned_data.get('machine')
        try:
            machine = int(machine)
        except ValueError:
            raise forms.ValidationError("Invalid machine number.")
        
        # Check if the machine number is in the list of valid choices
        machine_choices = [choice[0] for choice in ToolLifeData.MACHINE_NUMBER_CHOICES]
        if machine not in machine_choices:
            available_choices = ', '.join(str(choice) for choice in machine_choices)
            raise forms.ValidationError(
                f"Select a valid choice. {machine} is not one of the available choices. "
                f"Available choices are: {available_choices}"
            )
        return machine

    def clean_operation(self):
        """
        Validate the operation field to ensure it is a valid choice.

        Returns:
            int: Validated operation number.

        Raises:
            forms.ValidationError: If the operation number is invalid.
        """
        operation = self.cleaned_data.get('operation')
        try:
            operation = int(operation)
        except ValueError:
            raise forms.ValidationError("Invalid operation number.")
        
        # Check if the operation number is in the list of valid choices
        operation_choices = [choice[0] for choice in ToolLifeData.OPERATION_CHOICES]
        if operation not in operation_choices:
            available_choices = ', '.join(str(choice) for choice in operation_choices)
            raise forms.ValidationError(
                f"Select a valid choice. {operation} is not one of the available choices. "
                f"Available choices are: {available_choices}"
            )
        return operation

    def clean(self):
        """
        Clean the entire form and apply any additional validation needed.

        Returns:
            dict: Cleaned data.
        """
        cleaned_data = super(ToolLifeDataForm, self).clean()
        return cleaned_data
