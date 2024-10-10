from django.shortcuts import render, redirect, get_object_or_404
from .forms import FORM_TYPE_FORMS, OISQuestionForm
from .models import FormType, Form, FormQuestion
from django.forms import modelformset_factory
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView


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


# View to create form and its questions
def form_create_view(request):
    form_type_id = request.GET.get('form_type')

    if form_type_id:
        form_type = get_object_or_404(FormType, id=form_type_id)
        form_class = FORM_TYPE_FORMS.get(form_type.name)

        if form_class is None:
            return render(request, 'forms/error.html', {'message': 'Form type not supported.'})

        # Create a formset for the questions
        QuestionFormSet = modelformset_factory(FormQuestion, form=OISQuestionForm, extra=1, can_delete=True)

        if request.method == 'POST':
            form = form_class(request.POST)
            question_formset = QuestionFormSet(request.POST, queryset=FormQuestion.objects.none())

            if form.is_valid() and question_formset.is_valid():
                form_instance = form.save()

                # Save questions linked to the form
                for question_form in question_formset:
                    if question_form.cleaned_data and not question_form.cleaned_data.get('DELETE', False):
                        question_data = {
                            "Done by": question_form.cleaned_data.get('done_by'),
                            "Feature": question_form.cleaned_data.get('feature'),
                            "Sample Size": question_form.cleaned_data.get('sample_size'),
                            "Characteristic": question_form.cleaned_data.get('characteristic'),
                            "Special Characteristic": question_form.cleaned_data.get('special_characteristic'),
                            "Specifications": question_form.cleaned_data.get('specifications'),
                            "Sample Frequency": question_form.cleaned_data.get('sample_frequency')
                        }

                        # Create a new FormQuestion instance and link it to the form
                        question = FormQuestion(
                            form=form_instance,
                            question=question_data  # Store the dictionary in JSONField
                        )
                        question.save()  # Save the question to the database

                return redirect('form_create')  # Redirect after successful creation

        else:
            form = form_class()
            question_formset = QuestionFormSet(queryset=FormQuestion.objects.none())

        return render(request, 'forms/form_create.html', {
            'form': form,
            'question_formset': question_formset,
            'form_type': form_type
        })

    # If no form_type is selected, show form type selection page
    form_types = FormType.objects.all()
    return render(request, 'forms/select_form_type.html', {'form_types': form_types})
