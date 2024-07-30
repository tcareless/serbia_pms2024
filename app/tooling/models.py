from django.db import models

from django.db import models

class ToolLifeData(models.Model):
    form_definition = models.ForeignKey('FormDefinition', on_delete=models.CASCADE)
    data = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.form_definition.name} - {self.created_at.strftime('%Y-%m-%d %H:%M:%S')}"


class FormDefinition(models.Model):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

    def get_fields_with_options(self):
        fields_with_options = []
        for field in self.fields.all():
            options = list(field.options.values_list('option_value', flat=True))
            fields_with_options.append({
                'name': field.name,
                'label': field.label,
                'field_type': field.field_type,
                'is_required': field.is_required,
                'options': options
            })
        return fields_with_options



class FormField(models.Model):
    TEXT = 'text'
    NUMBER = 'number'
    SELECT = 'select'
    FIELD_TYPES = [
        (TEXT, 'Text'),
        (NUMBER, 'Number'),
        (SELECT, 'Select'),
    ]

    form_definition = models.ForeignKey(FormDefinition, related_name='fields', on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    label = models.CharField(max_length=255)
    field_type = models.CharField(max_length=50, choices=FIELD_TYPES)
    is_required = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.form_definition.name} - {self.label}"


class FieldOption(models.Model):
    form_field = models.ForeignKey(FormField, related_name='options', on_delete=models.CASCADE)
    option_value = models.CharField(max_length=255)

    def __str__(self):
        return self.option_value
