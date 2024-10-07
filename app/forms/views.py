from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from .models import FormType, Form, FormQuestion, FormAnswer


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


class FormCreateView(CreateView):
    model = Form
    fields = ['name', 'form_type']
    template_name = 'forms/forms/form_form.html'
    success_url = reverse_lazy('form_list')


class FormUpdateView(UpdateView):
    model = Form
    fields = ['name', 'form_type']
    template_name = 'forms/forms/form_form.html'
    success_url = reverse_lazy('form_list')


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



from .forms import QuestionForm

class QuestionCreateView(CreateView):
    model = FormQuestion
    form_class = QuestionForm
    template_name = 'forms/qa/question_form.html'

    def form_valid(self, form):
        # Combine fields into a JSON structure before saving
        question_data = {
            'Feature': form.cleaned_data['feature'],
            'Characteristic': form.cleaned_data['characteristic'],
            'Specifications': form.cleaned_data['specifications'],
            'Sample Frequency': form.cleaned_data['sample_frequency'],
            'Sample Size': form.cleaned_data['sample_size'],
            'Done by': form.cleaned_data['done_by'],
        }
        form.instance.question = question_data
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('question_list', kwargs={'form_id': self.object.form.id})

import json


class QuestionCreateView(CreateView):
    model = FormQuestion
    form_class = QuestionForm
    template_name = 'forms/qa/question_form.html'

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Set the form field based on the URL parameter form_id (passed via kwargs)
        form_id = self.kwargs['form_id']
        form.instance.form = get_object_or_404(Form, id=form_id)
        return form

    def form_valid(self, form):
        print("DEBUG: form_valid method triggered")

        question_data = {
            'Feature': form.cleaned_data.get('feature', ''),
            'Characteristic': form.cleaned_data.get('characteristic', ''),
            'Specifications': form.cleaned_data.get('specifications', ''),
            'Sample Frequency': form.cleaned_data.get('sample_frequency', ''),
            'Sample Size': form.cleaned_data.get('sample_size', ''),
            'Done by': form.cleaned_data.get('done_by', ''),
        }
        print(f"DEBUG: Question data to be saved as JSON: {json.dumps(question_data)}")

        form.instance.question = question_data
        response = super().form_valid(form)
        print(f"DEBUG: Form successfully saved with ID: {form.instance.id}")
        return response

    def get_success_url(self):
        return reverse_lazy('question_list', kwargs={'form_id': self.object.form.id})






class QuestionUpdateView(UpdateView):
    model = FormQuestion
    form_class = QuestionForm
    template_name = 'forms/qa/question_form.html'

    def get_initial(self):
        # Get the existing question data from the object (which is stored as JSON)
        initial = super().get_initial()
        question_data = self.object.question  # Assuming question is stored as JSON in the `question` field

        # Populate the initial values for the form fields
        initial['feature'] = question_data.get('Feature', '')
        initial['characteristic'] = question_data.get('Characteristic', '')
        initial['specifications'] = question_data.get('Specifications', '')
        initial['sample_frequency'] = question_data.get('Sample Frequency', '')
        initial['sample_size'] = question_data.get('Sample Size', '')
        initial['done_by'] = question_data.get('Done by', '')

        return initial

    def form_valid(self, form):
        # Combine fields into a JSON structure before saving
        question_data = {
            'Feature': form.cleaned_data['feature'],
            'Characteristic': form.cleaned_data['characteristic'],
            'Specifications': form.cleaned_data['specifications'],
            'Sample Frequency': form.cleaned_data['sample_frequency'],
            'Sample Size': form.cleaned_data['sample_size'],
            'Done by': form.cleaned_data['done_by'],
        }
        form.instance.question = question_data
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('question_list', kwargs={'form_id': self.object.form.id})



class QuestionDeleteView(DeleteView):
    model = FormQuestion
    template_name = 'forms/qa/question_confirm_delete.html'

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
