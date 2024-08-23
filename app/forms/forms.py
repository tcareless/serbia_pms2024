from django import forms
from .models import FormType
from .models import Form, FormQuestionAnswer


class FormTypeForm(forms.ModelForm):
    class Meta:
        model = FormType
        fields = ['name', 'template_name']


class FormForm(forms.ModelForm):
    class Meta:
        model = Form
        fields = ['name', 'form_type']


class FormQuestionAnswerForm(forms.ModelForm):
    class Meta:
        model = FormQuestionAnswer
        fields = ['question', 'answer_type', 'options']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['options'].widget = forms.HiddenInput()
        
        # Add an event listener for the answer_type field to show the options input when needed
        self.fields['answer_type'].widget.attrs.update({
            'onchange': 'showOptionsInput(this.value);'
        })