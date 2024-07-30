from django import forms
from .models import FormDefinition, FormField, FieldOption, ToolLifeData

class FormDefinitionForm(forms.ModelForm):
    class Meta:
        model = FormDefinition
        fields = ['name', 'description']

class FormFieldForm(forms.ModelForm):
    class Meta:
        model = FormField
        fields = ['name', 'label', 'field_type', 'is_required']

class FieldOptionForm(forms.ModelForm):
    class Meta:
        model = FieldOption
        fields = ['option_value']

class DynamicForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        form_definition = kwargs.pop('form_definition')
        super(DynamicForm, self).__init__(*args, **kwargs)
        self.fields['data'] = forms.JSONField(widget=forms.HiddenInput(), required=False)
        
        for field in form_definition.fields.all():
            field_name = f'field_{field.id}'
            if field.field_type == 'text':
                self.fields[field_name] = forms.CharField(label=field.label, required=field.is_required)
            elif field.field_type == 'number':
                self.fields[field_name] = forms.IntegerField(label=field.label, required=field.is_required)
            elif field.field_type == 'select':
                # Fetch the options for this field and create a list of tuples for choices
                choices = [(option.option_value, option.option_value) for option in field.options.all()]
                self.fields[field_name] = forms.ChoiceField(choices=choices, label=field.label, required=field.is_required)

    class Meta:
        model = ToolLifeData
        fields = []
