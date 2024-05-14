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
            'machine': forms.NumberInput(attrs={'min': 1, 'step': 1}),
            'operation': forms.NumberInput(attrs={'min': 1, 'step': 1}),
        }

    def __init__(self, *args, **kwargs):
        super(ToolLifeDataForm, self).__init__(*args, **kwargs)
        self.fields['machine'].choices = ToolLifeData.MACHINE_NUMBER_CHOICES
        self.fields['operation'].choices = ToolLifeData.OPERATION_CHOICES
        self.fields['shift'].choices = ToolLifeData.SHIFT_CHOICES
        self.fields['tool_type'].choices = ToolLifeData.TOOL_TYPE_CHOICES
        self.fields['tool_issue'].choices = ToolLifeData.TOOL_ISSUE_CHOICES

        # Debugging choices
        print("Initialized machine choices:", self.fields['machine'].choices)
        print("Initialized operation choices:", self.fields['operation'].choices)

    def clean_machine(self):
        machine = self.cleaned_data.get('machine')
        print(f"Raw machine input: {machine}")
        try:
            machine = int(machine)
            print(f"Converted machine to int: {machine}")
        except ValueError:
            raise forms.ValidationError("Invalid machine number.")
        machine_choices = [choice[0] for choice in ToolLifeData.MACHINE_NUMBER_CHOICES]
        print(f"Available machine choices: {machine_choices}")
        if machine not in machine_choices:
            available_choices = ', '.join(str(choice) for choice in machine_choices)
            raise forms.ValidationError(f"Select a valid choice. {machine} is not one of the available choices. Available choices are: {available_choices}")
        return machine

    def clean_operation(self):
        operation = self.cleaned_data.get('operation')
        print(f"Raw operation input: {operation}")
        try:
            operation = int(operation)
            print(f"Converted operation to int: {operation}")
        except ValueError:
            raise forms.ValidationError("Invalid operation number.")
        operation_choices = [choice[0] for choice in ToolLifeData.OPERATION_CHOICES]
        print(f"Available operation choices: {operation_choices}")
        if operation not in operation_choices:
            available_choices = ', '.join(str(choice) for choice in operation_choices)
            raise forms.ValidationError(f"Select a valid choice. {operation} is not one of the available choices. Available choices are: {available_choices}")
        return operation

    def clean(self):
        cleaned_data = super(ToolLifeDataForm, self).clean()
        return cleaned_data
