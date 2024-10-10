from django import forms
from .models import Form, FormQuestion, FormType

# OIS Form
class OISForm(forms.ModelForm):
    part_number = forms.CharField(max_length=255, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    operation = forms.CharField(max_length=255, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    part_name = forms.CharField(max_length=255, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    year = forms.CharField(max_length=4, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    mod_level = forms.CharField(max_length=255, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    machine = forms.CharField(max_length=255, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    mod_date = forms.DateField(required=True, widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}))

    class Meta:
        model = Form
        fields = ['name']

    def save(self, commit=True):
        form_instance = super().save(commit=False)
        form_instance.form_type = FormType.objects.get(name="OIS")
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





# OIS Question form
class OISQuestionForm(forms.ModelForm):
    feature = forms.CharField(max_length=255, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    special_characteristic = forms.CharField(max_length=255, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    characteristic = forms.CharField(max_length=255, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    specifications = forms.CharField(max_length=255, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    sample_frequency = forms.CharField(max_length=255, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    sample_size = forms.CharField(max_length=255, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    done_by = forms.CharField(max_length=255, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))

    class Meta:
        model = FormQuestion
        fields = ['feature', 'special_characteristic', 'characteristic', 'specifications', 'sample_frequency', 'sample_size', 'done_by']




from django import forms
from .models import Form, FormType

# Updated SampleForm with different fields than OISForm
class SampleForm(forms.ModelForm):
    project_name = forms.CharField(max_length=255, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    description = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4}), required=True)
    start_date = forms.DateField(required=True, widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}))
    end_date = forms.DateField(required=True, widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}))
    budget = forms.DecimalField(max_digits=10, decimal_places=2, required=True, widget=forms.NumberInput(attrs={'class': 'form-control'}))
    team_lead = forms.CharField(max_length=255, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    department = forms.CharField(max_length=255, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))

    class Meta:
        model = Form
        fields = ['name']

    def save(self, commit=True):
        form_instance = super().save(commit=False)
        form_instance.form_type = FormType.objects.get(name="SampleForm")
        form_instance.metadata = {
            'project_name': self.cleaned_data['project_name'],
            'description': self.cleaned_data['description'],
            'start_date': self.cleaned_data['start_date'].isoformat(),
            'end_date': self.cleaned_data['end_date'].isoformat(),
            'budget': str(self.cleaned_data['budget']),  # convert to string for JSON compatibility
            'team_lead': self.cleaned_data['team_lead'],
            'department': self.cleaned_data['department'],
        }
        if commit:
            form_instance.save()
        return form_instance


from django import forms
from .models import FormQuestion

# Updated SampleQuestionForm with different fields than OISQuestionForm
class SampleQuestionForm(forms.ModelForm):
    question_text = forms.CharField(max_length=255, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    measurement_type = forms.ChoiceField(choices=[('length', 'Length'), ('weight', 'Weight'), ('temperature', 'Temperature')], required=True, widget=forms.Select(attrs={'class': 'form-control'}))
    methodology = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}), required=True)
    frequency = forms.CharField(max_length=255, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    responsible_person = forms.CharField(max_length=255, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))

    class Meta:
        model = FormQuestion
        fields = ['question_text', 'measurement_type', 'methodology', 'frequency', 'responsible_person']




# Dictionary for dynamically mapping form types to form classes
FORM_TYPE_FORMS = {
    'OIS': OISForm,
    'SampleForm': SampleForm,  # Updated SampleForm here
}

# Dictionary for dynamically mapping form types to question form classes
QUESTION_FORM_CLASSES = {
    'OIS': OISQuestionForm,
    'SampleForm': SampleQuestionForm,  # Updated SampleQuestionForm here
}
