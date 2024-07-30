from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from .models import FormDefinition, FormField, FieldOption, ToolLifeData
from .forms import FormDefinitionForm, FormFieldForm, FieldOptionForm, DynamicForm
from django.views.generic.edit import CreateView
from django.http import JsonResponse


# FormDefinition Views
class FormListView(ListView):
    model = FormDefinition
    template_name = 'tooling/form_list.html'

class FormDetailView(DetailView):
    model = FormDefinition
    template_name = 'tooling/form_detail.html'

class FormCreateView(CreateView):
    model = FormDefinition
    form_class = FormDefinitionForm
    template_name = 'tooling/form_form.html'
    success_url = reverse_lazy('tooling:form_list')

class FormUpdateView(UpdateView):
    model = FormDefinition
    form_class = FormDefinitionForm
    template_name = 'tooling/form_form.html'
    success_url = reverse_lazy('tooling:form_list')

class FormDeleteView(DeleteView):
    model = FormDefinition
    template_name = 'tooling/form_confirm_delete.html'
    success_url = reverse_lazy('tooling:form_list')

# FormField Views
class FieldCreateView(CreateView):
    model = FormField
    form_class = FormFieldForm
    template_name = 'tooling/field_form.html'

    def form_valid(self, form):
        form.instance.form_definition_id = self.kwargs['form_id']
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_field_id'] = self.kwargs['form_id']
        context['options'] = []  # No options yet since it's a new field
        return context

    def get_success_url(self):
        return reverse_lazy('tooling:form_detail', kwargs={'pk': self.object.form_definition_id})


class FieldUpdateView(UpdateView):
    model = FormField
    form_class = FormFieldForm
    template_name = 'tooling/field_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_field_id'] = self.object.id
        context['options'] = self.object.options.all()
        return context

    def get_success_url(self):
        return reverse_lazy('tooling:form_detail', kwargs={'pk': self.object.form_definition_id})

class FieldDeleteView(DeleteView):
    model = FormField
    template_name = 'tooling/field_confirm_delete.html'

    def get_success_url(self):
        return reverse_lazy('tooling:form_detail', kwargs={'pk': self.object.form_definition_id})

# FieldOption Views
class OptionCreateView(CreateView):
    model = FieldOption
    form_class = FieldOptionForm
    template_name = 'tooling/option_form.html'

    def form_valid(self, form):
        form.instance.form_field_id = self.kwargs['field_id']
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('tooling:field_edit', kwargs={'pk': self.object.form_field_id})

class OptionUpdateView(UpdateView):
    model = FieldOption
    form_class = FieldOptionForm
    template_name = 'tooling/option_form.html'

    def get_success_url(self):
        return reverse_lazy('tooling:field_edit', kwargs={'pk': self.object.form_field_id})

class OptionDeleteView(DeleteView):
    model = FieldOption
    template_name = 'tooling/option_confirm_delete.html'

    def get_success_url(self):
        return reverse_lazy('tooling:field_edit', kwargs={'pk': self.object.form_field_id})

class DynamicFormView(CreateView):
    model = ToolLifeData
    form_class = DynamicForm
    template_name = 'tooling/dynamic_form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        form_definition = FormDefinition.objects.get(pk=self.kwargs['form_id'])
        kwargs['form_definition'] = form_definition
        return kwargs

    def form_valid(self, form):
        # Assign the form definition to the instance
        form.instance.form_definition = FormDefinition.objects.get(pk=self.kwargs['form_id'])
        # Save the dynamic data as JSON in the 'data' field
        form.instance.data = form.cleaned_data['data']
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form_definition = FormDefinition.objects.get(pk=self.kwargs['form_id'])
        context['form_definition'] = form_definition

        # Initialize the list to store field details
        fields_with_details = []

        # Collecting field details without print statements
        for field in form_definition.fields.all():
            options = list(field.options.values_list('option_value', flat=True))
            fields_with_details.append({
                'name': field.name,
                'label': field.label,
                'field_type': field.field_type,
                'is_required': field.is_required,
                'options': options
            })

        context['fields_with_details'] = fields_with_details

        return context

    def get_success_url(self):
        return reverse_lazy('tooling:form_list')


class HomePageView(ListView):
    model = FormDefinition
    template_name = 'tooling/home.html'
    context_object_name = 'forms'