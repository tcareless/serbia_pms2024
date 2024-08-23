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
        fields = ['question', 'answer']