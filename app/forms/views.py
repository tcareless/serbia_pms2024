from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from .models import FormType, Form, FormQuestion, FormAnswer
import json


# CRUD for FormType
class FormTypeListView(ListView):
    model = FormType
    template_name = 'forms/formtypes/formtype_list.html'
    context_object_name = 'formtypes'


class FormTypeCreateView(CreateView):
    model = FormType
    fields = ['name', 'template_name']
    template_name = 'forms/formtypes/formtype_form.html'
    success_url = reverse_lazy('formtype_list')


class FormTypeUpdateView(UpdateView):
    model = FormType
    fields = ['name', 'template_name']
    template_name = 'forms/formtypes/formtype_form.html'
    success_url = reverse_lazy('formtype_list')


class FormTypeDeleteView(DeleteView):
    model = FormType
    template_name = 'forms/formtypes/formtype_confirm_delete.html'
    success_url = reverse_lazy('formtype_list')


# CRUD for Form
class FormListView(ListView):
    model = Form
    template_name = 'forms/forms/form_list.html'
    context_object_name = 'forms'


from django import forms


    

class FormUpdateView(UpdateView):
    model = Form
    fields = ['name', 'form_type', 'metadata']  # Include metadata field
    template_name = 'forms/forms/form_form.html'
    success_url = reverse_lazy('form_list')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)

        # Customize the metadata field widget if needed
        form.fields['metadata'] = forms.JSONField(widget=forms.Textarea, required=False)

        # Pass the current metadata to the form so it can be used in the template
        form.initial['metadata'] = self.object.metadata  # Pass existing metadata as initial value
        return form




class FormDeleteView(DeleteView):
    model = Form
    template_name = 'forms/forms/form_confirm_delete.html'
    success_url = reverse_lazy('form_list')


from django.shortcuts import get_object_or_404
from .models import Form, FormQuestion

class QuestionListView(ListView):
    model = FormQuestion
    template_name = 'forms/qa/question_list.html'
    context_object_name = 'questions'

    def get_queryset(self):
        # Filter questions by form_id
        return FormQuestion.objects.filter(form_id=self.kwargs['form_id'])

    def get_context_data(self, **kwargs):
        # Add form object to the context
        context = super().get_context_data(**kwargs)
        context['form'] = get_object_or_404(Form, id=self.kwargs['form_id'])
        return context



from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.views.generic import TemplateView
from .forms import OISForm, OISQuestionForm
from django.template.loader import render_to_string


# Main view for rendering the initial page and handling form submissions
class DynamicFormCreateView(TemplateView):
    template_name = 'forms/dynamic_form.html'

    def get_form(self, form_class=None):
        return None  # Prevent form loading on initial GET

    def post(self, request, *args, **kwargs):
        form_type = request.POST.get('form_type')

        # Print debug information to see what form_type is being passed
        print(f"Form Type Received: {form_type}")
        print(f"POST Data: {request.POST}")

        # Load the appropriate form class based on form_type
        if form_type == 'ois':
            form = OISForm(request.POST)
            question_form = OISQuestionForm(request.POST)
        else:
            return JsonResponse({'error': 'Invalid form type'}, status=400)

        # Check if both the main form and the question form are valid
        if form.is_valid() and question_form.is_valid():
            # Save the main form instance
            form_instance = form.save()

            # Collect all question fields and save as JSON
            question_data = {
                'feature': question_form.cleaned_data['feature'],
                'special_characteristic': question_form.cleaned_data['special_characteristic'],
                'characteristic': question_form.cleaned_data['characteristic'],
                'specifications': question_form.cleaned_data['specifications'],
                'sample_frequency': question_form.cleaned_data['sample_frequency'],
                'sample_size': question_form.cleaned_data['sample_size'],
                'done_by': question_form.cleaned_data['done_by'],
            }

            # Save the question form, linking it to the saved form instance
            question_instance = question_form.save(commit=False)
            question_instance.form = form_instance  # Link the form to the question
            question_instance.question = question_data  # Save question as JSON
            question_instance.save()

            # Redirect or respond with a success message
            return redirect('form_list')  # Redirect after successful submission
        else:
            # If there are errors, re-render the form with validation errors
            return render(request, self.template_name, {
                'form': form,
                'question_form': question_form,
            })







# AJAX view to dynamically load the form fields
def load_form_fields(request):
    form_type = request.GET.get('form_type')

    # Load the appropriate form based on form_type
    if form_type == 'ois':
        form = OISForm()
        question_form = OISQuestionForm()
    else:
        form = None
        question_form = None

    # Render the forms as HTML
    form_html = render_to_string('forms/form_fields.html', {'form': form, 'question_form': question_form}, request=request)

    return JsonResponse({'form_html': form_html})








class QuestionDeleteView(DeleteView):
    model = FormQuestion
    template_name = 'forms/qa/question_confirm_delete.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = self.object.form  # Ensure form is available in the context
        return context

    def get_success_url(self):
        return reverse_lazy('question_list', kwargs={'form_id': self.object.form.id})



# CRUD for Answers (FormAnswer)
class AnswerListView(ListView):
    model = FormAnswer
    template_name = 'forms/qa/answer_list.html'
    context_object_name = 'answers'

    def get_queryset(self):
        return FormAnswer.objects.filter(question_id=self.kwargs['question_id'])


class AnswerCreateView(CreateView):
    model = FormAnswer
    fields = ['question', 'answer']
    template_name = 'forms/qa/answer_form.html'

    def get_success_url(self):
        return reverse_lazy('answer_list', kwargs={'question_id': self.object.question.id})


class AnswerUpdateView(UpdateView):
    model = FormAnswer
    fields = ['question', 'answer']
    template_name = 'forms/qa/answer_form.html'

    def get_success_url(self):
        return reverse_lazy('answer_list', kwargs={'question_id': self.object.question.id})


class AnswerDeleteView(DeleteView):
    model = FormAnswer
    template_name = 'forms/qa/answer_confirm_delete.html'

    def get_success_url(self):
        return reverse_lazy('answer_list', kwargs={'question_id': self.object.question.id})





# ==============================================================
# ==============================================================
# =================== Some Tests ===============================
# ==============================================================
# ==============================================================


from django.shortcuts import render, get_object_or_404, redirect
from .models import Form, FormQuestion, FormAnswer
from django.utils import timezone

def ois_form_view(request, form_id):
    # Get the OIS form object based on the form_id
    form = get_object_or_404(Form, id=form_id)
    
    # Fetch all the questions related to the OIS form
    questions = form.questions.all()

    if request.method == "POST":
        # Loop through all the questions and save the answers
        for question in questions:
            # Get the answer from the form submission
            answer_data = request.POST.get(f'answer_{question.id}')

            # Create a new FormAnswer object for each question
            FormAnswer.objects.create(
                question=question,
                answer={"result": answer_data},  # Storing answer as JSON, you can modify this structure if needed
                created_at=timezone.now()
            )
        
        # Redirect after submission to avoid re-submission on page refresh
        return redirect('ois_form', form_id=form_id)
    
    # Prepare data for display
    question_list = []
    for question in questions:
        question_data = {
            'feature': question.question.get('Feature'),
            'characteristic': question.question.get('Characteristic'),
            'specifications': question.question.get('Specifications'),
            'sample_frequency': question.question.get('Sample Frequency'),
            'sample_size': question.question.get('Sample Size'),
            'done_by': question.question.get('Done by')
        }
        question_list.append({'question': question, **question_data})

    # Render the template with the form and modified questions
    return render(request, 'forms/ois_form_template.html', {'form': form, 'questions': question_list})
