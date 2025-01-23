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



# TPM Form
class TPMForm(forms.ModelForm):
    part_number = forms.CharField(max_length=255, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    operation = forms.CharField(max_length=255, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))

    class Meta:
        model = Form
        fields = ['name']  # Assuming 'name' is a standard field for all forms

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.metadata:
            # Prepopulate fields from the metadata JSON
            self.fields['part_number'].initial = self.instance.metadata.get('part_number', '')
            self.fields['operation'].initial = self.instance.metadata.get('operation', '')

    def save(self, commit=True):
        form_instance = super().save(commit=False)
        form_instance.form_type = FormType.objects.get(name="TPM")  # Assuming FormType for TPM exists
        form_instance.metadata = {
            'part_number': self.cleaned_data['part_number'],
            'operation': self.cleaned_data['operation'],
        }
        if commit:
            form_instance.save()
        return form_instance


# Updated TPM Question Form with order field
class TPMQuestionForm(forms.ModelForm):
    question_text = forms.CharField(
        max_length=255,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter a question'})
    )
    order = forms.IntegerField(
        widget=forms.HiddenInput(), 
        required=False, 
        initial=1  # Default value for order if not provided
    )

    class Meta:
        model = FormQuestion
        fields = ['question_text', 'order']  # Include order field

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.question:
            # Prepopulate the field from the question JSON
            self.fields['question_text'].initial = self.instance.question.get('question_text', '')
            self.fields['order'].initial = self.instance.question.get('order', 1)  # Get 'order' from JSON, default to 1

    def save(self, form_instance=None, order=None, commit=True):
        question_instance = super().save(commit=False)
        if form_instance:
            question_instance.form = form_instance
        # Build the question data
        question_data = {
            'question_text': self.cleaned_data['question_text'],
            'order': order if order is not None else self.cleaned_data.get('order', 1),  # Use provided order or fallback to field value
        }
        question_instance.question = question_data
        if commit:
            question_instance.save()
        return question_instance


# LPA Form
class LPAForm(forms.ModelForm):
    part_number = forms.CharField(max_length=255, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    operation = forms.CharField(max_length=255, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))

    class Meta:
        model = Form
        fields = ['name']  # Assuming 'name' is a standard field for all forms

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.metadata:
            # Prepopulate fields from the metadata JSON
            self.fields['part_number'].initial = self.instance.metadata.get('part_number', '')
            self.fields['operation'].initial = self.instance.metadata.get('operation', '')

    def save(self, commit=True):
        form_instance = super().save(commit=False)
        form_instance.form_type = FormType.objects.get(name="LPA")  # Assuming FormType for LPA exists
        form_instance.metadata = {
            'part_number': self.cleaned_data['part_number'],
            'operation': self.cleaned_data['operation'],
        }
        if commit:
            form_instance.save()
        return form_instance


class LPAQuestionForm(forms.ModelForm):
    question_text = forms.CharField(
        max_length=255,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter a question'})
    )
    what_to_look_for = forms.CharField(
        max_length=255,
        required=False,  # Optional
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter what to look for (optional)'})
    )
    recommended_action = forms.CharField(
        max_length=255,
        required=False,  # Optional
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter recommended action (optional)'})
    )
    typed_answer = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    order = forms.IntegerField(
        widget=forms.HiddenInput(),
        required=False,
        initial=1  # Default value for order if not provided
    )

    class Meta:
        model = FormQuestion
        fields = ['question_text', 'what_to_look_for', 'recommended_action', 'typed_answer', 'order']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.question:
            # Prepopulate the fields from the question JSON
            self.fields['question_text'].initial = self.instance.question.get('question_text', '')
            self.fields['what_to_look_for'].initial = self.instance.question.get('what_to_look_for', '')
            self.fields['recommended_action'].initial = self.instance.question.get('recommended_action', '')
            self.fields['typed_answer'].initial = self.instance.question.get('typed_answer', False)  # Prepopulate the checkbox
            self.fields['order'].initial = self.instance.question.get('order', 1)

    def save(self, form_instance=None, order=None, commit=True):
        question_instance = super().save(commit=False)
        if form_instance:
            question_instance.form = form_instance
        # Build the question data
        question_data = {
            'question_text': self.cleaned_data['question_text'],
            'what_to_look_for': self.cleaned_data.get('what_to_look_for', ''),
            'recommended_action': self.cleaned_data.get('recommended_action', ''),
            'typed_answer': self.cleaned_data.get('typed_answer', False),  # Add the checkbox value to the JSON
            'order': order if order is not None else self.cleaned_data.get('order', 1),
        }
        question_instance.question = question_data
        if commit:
            question_instance.save()
        return question_instance




# Dictionary for dynamically mapping form types to form classes
FORM_TYPE_FORMS = {
    'OIS': OISForm,
    'TPM': TPMForm,  # Added TPM form
    'LPA': LPAForm,
}

# Dictionary for dynamically mapping form types to question form classes
QUESTION_FORM_CLASSES = {
    'OIS': OISQuestionForm,
    'TPM': TPMQuestionForm,  # Added TPM question form
    'LPA': LPAQuestionForm,
}










from django.core.exceptions import ValidationError
from django import forms
from .models import FormAnswer

class OISAnswerForm(forms.ModelForm):
    class Meta:
        model = FormAnswer
        fields = ['answer']

    def __init__(self, *args, question=None, **kwargs):
        """Adjust the answer field based on whether the question requires a checkmark."""
        super().__init__(*args, **kwargs)
        if question and question.question.get('checkmark', False):  # Use dropdown for checkmark questions
            self.fields['answer'] = forms.ChoiceField(
                choices=[('', 'Select...'), ('Pass', 'Pass'), ('Fail', 'Fail')],
                widget=forms.Select(attrs={'class': 'form-select'})  # Use Bootstrap's form-select for styling
            )
        else:
            # Default to a text input for non-checkmark questions
            self.fields['answer'] = forms.CharField(
                max_length=255,
                required=True,
                widget=forms.TextInput(attrs={
                    'class': 'form-control input-box',
                    'style': 'width: 100px;',
                    'placeholder': 'Answer'
                })
            )



class LPAAnswerForm(forms.ModelForm):
    """
    Form for capturing Yes/No answers for LPA questions,
    with fields for 'Issue', 'Action Taken', and an additional char input field.
    """
    answer = forms.ChoiceField(
        choices=[('', 'Select...'), ('Yes', 'Yes'), ('No', 'No')],
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=False
    )
    issue = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Describe the issue',
            'rows': 3
        })
    )
    action_taken = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Describe the action taken',
            'rows': 3
        })
    )
    additional_input = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Answer Here'
        })
    )

    class Meta:
        model = FormAnswer
        fields = ['answer']  # We'll dynamically store everything in 'answer'

    def __init__(self, *args, user=None, machine=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user  # Store the user in the form instance
        self.machine = machine  # Store the machine in the form instance

    def clean(self):
        """
        Validate the form and ensure that at least one of 'answer' or 'additional_input' is provided.
        Also, include the username and machine in the answer JSON.
        """
        cleaned_data = super().clean()
        answer = cleaned_data.get('answer')
        issue = cleaned_data.get('issue')
        action_taken = cleaned_data.get('action_taken')
        additional_input = cleaned_data.get('additional_input')

        # Validate that at least one of 'answer' or 'additional_input' is provided
        if not answer and not additional_input:
            raise forms.ValidationError("You must provide either an answer (Yes/No) or additional input.")

        # Validate that 'issue' and 'action_taken' are provided if 'answer' is 'No'
        if answer == 'No':
            if not issue:
                self.add_error('issue', "This field is required when 'No' is selected.")
            if not action_taken:
                self.add_error('action_taken', "This field is required when 'No' is selected.")

        # Construct the answer JSON
        answer_data = {}
        if answer:
            answer_data['answer'] = answer
        if answer == 'No' and issue and action_taken:
            answer_data.update({
                'issue': issue,
                'action_taken': action_taken,
            })
        if additional_input:
            answer_data['answer'] = additional_input

        # Add submitted_by and machine to the answer data
        if self.user and self.user.is_authenticated:
            answer_data['submitted_by'] = self.user.username
        else:
            answer_data['submitted_by'] = 'Anonymous'

        if self.machine:
            answer_data['machine'] = self.machine  # Include the machine value in the JSON

        # Debug print to check the final answer JSON
        print(f"[DEBUG] Final answer data: {answer_data}")

        # Store the constructed JSON in the 'answer' field
        cleaned_data['answer'] = answer_data

        return cleaned_data