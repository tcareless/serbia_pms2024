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








from django.shortcuts import render, redirect, get_object_or_404
from .forms import FORM_TYPE_FORMS, OISQuestionForm
from .models import FormType, Form, FormQuestion
from django.forms import modelformset_factory
import json

def form_create_view(request):
    form_type_id = request.GET.get('form_type')

    if form_type_id:
        form_type = get_object_or_404(FormType, id=form_type_id)
        form_class = FORM_TYPE_FORMS.get(form_type.name)

        if form_class is None:
            return render(request, 'forms/error.html', {'message': 'Form type not supported.'})

        QuestionFormSet = modelformset_factory(FormQuestion, form=OISQuestionForm, extra=1, can_delete=True)

        if request.method == 'POST':
            form = form_class(request.POST)
            question_formset = QuestionFormSet(request.POST)

            if form.is_valid() and question_formset.is_valid():
                form_instance = form.save()

                # Save questions linked to the form
                for question_form in question_formset:
                    if question_form.cleaned_data:
                        # Construct the question dictionary directly
                        question_data = {
                            "Done by": question_form.cleaned_data.get('done_by'),
                            "Feature": question_form.cleaned_data.get('feature'),
                            "Sample Size": question_form.cleaned_data.get('sample_size'),
                            "Characteristic": question_form.cleaned_data.get('characteristic'),
                            "Special Characteristic": question_form.cleaned_data.get('special_characteristic'),  # if needed
                            "Specifications": question_form.cleaned_data.get('specifications'),  # if needed
                            "Sample Frequency": question_form.cleaned_data.get('sample_frequency')  # if needed
                        }

                        # Create a new FormQuestion instance
                        question = FormQuestion(
                            form=form_instance,  # Link to the form instance
                            question=question_data  # Store the dictionary directly in JSONField
                        )
                        question.save()  # Save the question to the database

                # Redirect after successful creation
                return redirect('form_create')  # Redirect to your desired page

        else:
            form = form_class()
            question_formset = QuestionFormSet(queryset=FormQuestion.objects.none())

        return render(request, 'forms/form_create.html', {
            'form': form,
            'question_formset': question_formset,
            'form_type': form_type
        })

    # If form_type is not selected, show a page to select form type
    form_types = FormType.objects.all()
    return render(request, 'forms/select_form_type.html', {'form_types': form_types})
