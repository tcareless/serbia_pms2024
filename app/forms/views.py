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
from django.shortcuts import render, redirect, get_object_or_404
from .forms import FORM_TYPE_FORMS, QUESTION_FORM_CLASSES
from .models import FormType, FormQuestion
from django.forms import modelformset_factory


# View to create form and its questions
# View to create form and its questions
def form_create_view(request):
    form_type_id = request.GET.get('form_type')

    if form_type_id:
        form_type = get_object_or_404(FormType, id=form_type_id)
        
        # Dynamically get the form class for the form type
        form_class = FORM_TYPE_FORMS.get(form_type.name)
        question_form_class = QUESTION_FORM_CLASSES.get(form_type.name)

        if form_class is None or question_form_class is None:
            return render(request, 'forms/error.html', {'message': 'Form type not supported.'})

        # Dynamically get fields for the question formset
        question_fields = question_form_class._meta.fields

        # Create a dynamic formset for questions with the fields from the question form
        QuestionFormSet = modelformset_factory(FormQuestion, form=question_form_class, fields=question_fields, extra=1)

        if request.method == 'POST':
            form = form_class(request.POST)
            question_formset = QuestionFormSet(request.POST)

            if form.is_valid() and question_formset.is_valid():
                form_instance = form.save()

                # Save questions dynamically
                for question_form in question_formset:
                    if question_form.cleaned_data:  # Handle only valid cleaned_data forms
                        # Exclude 'id' field from cleaned_data
                        question_data = {field: question_form.cleaned_data[field] for field in question_form.cleaned_data if field != 'id' and field != 'DELETE'}

                        # Create and save FormQuestion instance
                        question = FormQuestion(
                            form=form_instance,
                            question=question_data  # Store the dictionary in JSONField
                        )
                        question.save()

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
