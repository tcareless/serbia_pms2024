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
        self.form_definition = form_definition

        for field in form_definition.fields.all():
            field_name = f'field_{field.id}'
            if field.field_type == 'text' and field.options.exists():
                # If the field is text but has options, it should be a select field
                choices = [('', '---')] + [(option.option_value, option.option_value) for option in field.options.all()]
                self.fields[field_name] = forms.ChoiceField(
                    choices=choices,
                    label=field.label,
                    required=field.is_required
                )
            elif field.field_type == 'text':
                self.fields[field_name] = forms.CharField(
                    label=field.label,
                    required=field.is_required
                )
            elif field.field_type == 'number':
                self.fields[field_name] = forms.IntegerField(
                    label=field.label,
                    required=field.is_required
                )

    def clean(self):
        cleaned_data = super().clean()
        data_dict = {}
        for field in self.form_definition.fields.all():
            field_name = f'field_{field.id}'
            data_dict[field_name] = cleaned_data.get(field_name)
        self.cleaned_data['data'] = data_dict
        return self.cleaned_data

    class Meta:
        model = ToolLifeData
        fields = []