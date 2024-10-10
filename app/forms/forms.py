from django import forms
from .models import Form, FormQuestion, FormType

# OIS FormType specific form
class OISForm(forms.ModelForm):
    part_number = forms.CharField(
        max_length=255,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    operation = forms.CharField(
        max_length=255,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    part_name = forms.CharField(
        max_length=255,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    year = forms.CharField(
        max_length=4,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    mod_level = forms.CharField(
        max_length=255,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    machine = forms.CharField(
        max_length=255,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    mod_date = forms.DateField(
        required=True,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )

    class Meta:
        model = Form
        fields = ['name']  # Only the field(s) present in the Form model

    def save(self, commit=True):
        form_instance = super().save(commit=False)
        form_type = FormType.objects.get(name="OIS")
        form_instance.form_type = form_type
        form_instance.metadata = {
            'part_number': self.cleaned_data['part_number'],
            'operation': self.cleaned_data['operation'],
            'part_name': self.cleaned_data['part_name'],
            'year': self.cleaned_data['year'],
            'mod_level': self.cleaned_data['mod_level'],
            'machine': self.cleaned_data['machine'],
            'mod_date': self.cleaned_data['mod_date'].isoformat()
        }
        if commit:
            form_instance.save()
        return form_instance

class OISQuestionForm(forms.ModelForm):
    question = forms.CharField(
        max_length=255,  # Assuming the field to capture the question is called 'question'
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    feature = forms.CharField(max_length=255, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    special_characteristic = forms.CharField(max_length=255, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    characteristic = forms.CharField(max_length=255, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    specifications = forms.CharField(max_length=255, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    sample_frequency = forms.CharField(max_length=255, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    sample_size = forms.CharField(max_length=255, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    done_by = forms.CharField(max_length=255, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))

    class Meta:
        model = FormQuestion
        fields = ['question', 'feature', 'special_characteristic', 'characteristic', 'specifications', 'sample_frequency', 'sample_size', 'done_by']

# Mapping of form type names to form classes
FORM_TYPE_FORMS = {
    'OIS': OISForm,
    # Add additional form types here as needed, e.g.:
    # 'XYZForm': XYZFormClass
}
