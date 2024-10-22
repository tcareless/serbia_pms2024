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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.metadata:
            # Prepopulate fields from the metadata JSON
            self.fields['part_number'].initial = self.instance.metadata.get('part_number', '')
            self.fields['operation'].initial = self.instance.metadata.get('operation', '')
            self.fields['part_name'].initial = self.instance.metadata.get('part_name', '')
            self.fields['year'].initial = self.instance.metadata.get('year', '')
            self.fields['mod_level'].initial = self.instance.metadata.get('mod_level', '')
            self.fields['machine'].initial = self.instance.metadata.get('machine', '')
            self.fields['mod_date'].initial = self.instance.metadata.get('mod_date', '')

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
    order = forms.IntegerField(widget=forms.HiddenInput(), required=False)  # Hidden order field
    checkmark = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))  # New Checkmark field

    class Meta:
        model = FormQuestion
        fields = ['feature', 'special_characteristic', 'characteristic', 'specifications', 'sample_frequency', 'sample_size', 'done_by', 'order', 'checkmark']  # Include checkmark in fields

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.question:
            # Prepopulate fields from the question JSON
            self.fields['feature'].initial = self.instance.question.get('feature', '')
            self.fields['special_characteristic'].initial = self.instance.question.get('special_characteristic', '')
            self.fields['characteristic'].initial = self.instance.question.get('characteristic', '')
            self.fields['specifications'].initial = self.instance.question.get('specifications', '')
            self.fields['sample_frequency'].initial = self.instance.question.get('sample_frequency', '')
            self.fields['sample_size'].initial = self.instance.question.get('sample_size', '')
            self.fields['done_by'].initial = self.instance.question.get('done_by', '')
            self.fields['order'].initial = self.instance.question.get('order', 1)  # Get 'order' from JSON
            self.fields['checkmark'].initial = self.instance.question.get('checkmark', False)  # Get 'checkmark' from JSON, default to False

    def save(self, form_instance=None, order=None, commit=True):
        question_instance = super().save(commit=False)
        if form_instance:
            question_instance.form = form_instance
        # Build the question data
        question_data = {
            'feature': self.cleaned_data['feature'],
            'special_characteristic': self.cleaned_data['special_characteristic'],
            'characteristic': self.cleaned_data['characteristic'],
            'specifications': self.cleaned_data['specifications'],
            'sample_frequency': self.cleaned_data['sample_frequency'],
            'sample_size': self.cleaned_data['sample_size'],
            'done_by': self.cleaned_data['done_by'],
            'order': order if order is not None else self.cleaned_data.get('order', 1),
            'checkmark': self.cleaned_data['checkmark'],  # Add checkmark to the question data
        }
        question_instance.question = question_data
        if commit:
            question_instance.save()
        return question_instance



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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.metadata:
            # Prepopulate fields from the metadata JSON
            self.fields['project_name'].initial = self.instance.metadata.get('project_name', '')
            self.fields['description'].initial = self.instance.metadata.get('description', '')
            self.fields['start_date'].initial = self.instance.metadata.get('start_date', '')
            self.fields['end_date'].initial = self.instance.metadata.get('end_date', '')
            self.fields['budget'].initial = self.instance.metadata.get('budget', '')
            self.fields['team_lead'].initial = self.instance.metadata.get('team_lead', '')
            self.fields['department'].initial = self.instance.metadata.get('department', '')

    def save(self, form_instance=None, order=None, commit=True):
        question_instance = super().save(commit=False)
        if form_instance:
            question_instance.form = form_instance
        # Build the question data
        question_data = {
            'question_text': self.cleaned_data['question_text'],
            'measurement_type': self.cleaned_data['measurement_type'],
            'methodology': self.cleaned_data['methodology'],
            'frequency': self.cleaned_data['frequency'],
            'responsible_person': self.cleaned_data['responsible_person'],
            'order': order if order is not None else self.cleaned_data.get('order', 1),
        }
        question_instance.question = question_data
        if commit:
            question_instance.save()
        return question_instance



from django import forms
from .models import FormQuestion

# Updated SampleQuestionForm with different fields than OISQuestionForm
class SampleQuestionForm(forms.ModelForm):
    question_text = forms.CharField(max_length=255, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    measurement_type = forms.ChoiceField(choices=[('length', 'Length'), ('weight', 'Weight'), ('temperature', 'Temperature')], required=True, widget=forms.Select(attrs={'class': 'form-control'}))
    methodology = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}), required=True)
    frequency = forms.CharField(max_length=255, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    responsible_person = forms.CharField(max_length=255, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    order = forms.IntegerField(widget=forms.HiddenInput(), required=False)  # Hidden order field

    class Meta:
        model = FormQuestion
        fields = ['question_text', 'measurement_type', 'methodology', 'frequency', 'responsible_person', 'order']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.question:
            # Prepopulate fields from the question JSON
            self.fields['question_text'].initial = self.instance.question.get('question_text', '')
            self.fields['measurement_type'].initial = self.instance.question.get('measurement_type', '')
            self.fields['methodology'].initial = self.instance.question.get('methodology', '')
            self.fields['frequency'].initial = self.instance.question.get('frequency', '')
            self.fields['responsible_person'].initial = self.instance.question.get('responsible_person', '')
            self.fields['order'].initial = self.instance.question.get('order', 1)  # Get 'order' from JSON

    def save(self, commit=True):
        question_instance = super().save(commit=False)
        question_instance.question = {
            'question_text': self.cleaned_data['question_text'],
            'measurement_type': self.cleaned_data['measurement_type'],
            'methodology': self.cleaned_data['methodology'],
            'frequency': self.cleaned_data['frequency'],
            'responsible_person': self.cleaned_data['responsible_person'],
            'order': self.cleaned_data['order'],  # Save 'order' back to JSON
        }
        if commit:
            question_instance.save()
        return question_instance




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



from django import forms
from .models import FormAnswer

class OISAnswerForm(forms.ModelForm):
    answer = forms.CharField(
        max_length=255,  # You can adjust this based on the type of answers expected
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control input-box',  # Use Bootstrap classes for styling
            'style': 'width: 100px;',  # Control the size of the input field
            'placeholder': 'Enter answer'  # Provide a placeholder for clarity
        })
    )

    class Meta:
        model = FormAnswer
        fields = ['answer']
