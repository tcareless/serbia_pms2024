from django.shortcuts import render, redirect, get_object_or_404
from .forms import FORM_TYPE_FORMS, OISQuestionForm
from .models import FormType, Form, FormQuestion
from django.forms import modelformset_factory
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView



def index(request):
    return render(request, 'forms/index.html')


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
from .models import FormType, Form, FormQuestion
from django.forms import modelformset_factory

def form_create_view(request, form_id=None):
    form_instance = None
    form_type = None
    if form_id:
        # Fetch the existing form to edit
        form_instance = get_object_or_404(Form, id=form_id)
        form_type = form_instance.form_type
    else:
        # Fetch the form type from the request for new forms
        form_type_id = request.GET.get('form_type')
        if form_type_id:
            form_type = get_object_or_404(FormType, id=form_type_id)

    if form_type:
        # Dynamically get the form class for the form type
        form_class = FORM_TYPE_FORMS.get(form_type.name)
        question_form_class = QUESTION_FORM_CLASSES.get(form_type.name)

        if form_class is None or question_form_class is None:
            return render(request, 'forms/error.html', {'message': 'Form type not supported.'})

        # Create a dynamic formset for questions
        QuestionFormSet = modelformset_factory(
            FormQuestion,
            form=question_form_class,
            extra=0,  # Set extra to 0 to prevent empty forms unless added by the user
            can_delete=True  # Allow deletion of forms
        )

        if request.method == 'POST':
            form = form_class(request.POST, instance=form_instance)
            question_formset = QuestionFormSet(
                request.POST,
                queryset=form_instance.questions.order_by('question__order') if form_instance else FormQuestion.objects.none()
            )

            if form.is_valid() and question_formset.is_valid():
                form_instance = form.save()

                # Save each question in the formset
                for index, question_form in enumerate(question_formset.forms, start=1):
                    if question_form.cleaned_data and not question_form.cleaned_data.get('DELETE', False):
                        question_form.save(form_instance=form_instance, order=index)
                    elif question_form.cleaned_data.get('DELETE', False) and question_form.instance.pk:
                        # If the form is marked for deletion and exists in the DB, delete it
                        question_form.instance.delete()

                return redirect('form_edit', form_id=form_instance.id)  # Redirect after saving

        else:
            # Fetch questions ordered by the 'order' field in the JSON
            form = form_class(instance=form_instance)
            question_formset = QuestionFormSet(
                queryset=form_instance.questions.order_by('question__order') if form_instance else FormQuestion.objects.none()
            )

        return render(request, 'forms/form_create.html', {
            'form': form,
            'question_formset': question_formset,
            'form_type': form_type
        })

    # If no form_type is provided, show a page to select the form type
    form_types = FormType.objects.all()
    return render(request, 'forms/select_form_type.html', {'form_types': form_types})








# =============================================================================
# =============================================================================
# ======================= Find forms Now ======================================
# =============================================================================
# =============================================================================


from django.shortcuts import render, get_object_or_404
from .models import Form, FormType

def find_forms_view(request):
    # Get the form type ID from the request
    form_type_id = request.GET.get('form_type')

    if form_type_id:
        # Fetch the FormType object
        form_type = get_object_or_404(FormType, id=form_type_id)
        
        # Fetch the forms of that form type, ordering by created_at descending
        forms = Form.objects.filter(form_type_id=form_type_id).order_by('-created_at')
        
        return render(request, 'forms/find_forms.html', {
            'form_type': form_type,
            'forms': forms,
        })

    # If no form type is selected, display the form type selection
    form_types = FormType.objects.all()
    return render(request, 'forms/select_form_type.html', {
        'form_types': form_types,
    })














# ==============================================================================
# ==============================================================================
# ======================== Bulk insert tool ====================================
# ==============================================================================
# ==============================================================================


from django.shortcuts import render, redirect, get_object_or_404
from .models import Form, FormQuestion
import json

def bulk_question_create_view(request):
    if request.method == 'POST':
        form_id = request.POST.get('form_id')
        questions_json = request.POST.get('questions_json')
        delete_existing = request.POST.get('delete_existing') == 'on'

        # Get the form instance
        form_instance = get_object_or_404(Form, id=form_id)

        try:
            questions_data = json.loads(questions_json)
        except json.JSONDecodeError as e:
            # Handle JSON parsing error
            return render(request, 'forms/bulk_question_create.html', {
                'error': f'Invalid JSON data: {e}',
                'form_id': form_id,
                'questions_json': questions_json,
            })

        if delete_existing:
            # Delete existing questions for the form
            form_instance.questions.all().delete()

        # Iterate over the questions and create FormQuestion instances
        for index, question_data in enumerate(questions_data, start=1):
            # Ensure 'order' is set
            question_data['order'] = question_data.get('order', index)
            # Create the FormQuestion instance
            FormQuestion.objects.create(
                form=form_instance,
                question=question_data
            )

        return redirect('form_edit', form_id=form_instance.id)  # Redirect after saving

    else:
        return render(request, 'forms/bulk_question_create.html')




# The page is expecting a format like this:

# [
#   {
#     "feature": "67",
#     "special_characteristic": "Bu",
#     "characteristic": "Hub OD (Air Gauge)",
#     "specifications": "Ø30.187 - Ø30.213 mm",
#     "sample_frequency": "100%",
#     "sample_size": "100%",
#     "done_by": "OP/QA"
#   },
#   {
#     "feature": "HP",
#     "special_characteristic": "D",
#     "characteristic": "Hole(s) Presence (Visual/Gauge)",
#     "specifications": "Present YES / NO",
#     "sample_frequency": "100%",
#     "sample_size": "100%",
#     "done_by": "OP / QA"
#   }
#   // ... add more questions as needed ...
# ]












# ==================================================================
# ==================================================================
# ================= Operator Form Template OIS =====================
# ==================================================================
# ==================================================================


from django.shortcuts import render, get_object_or_404, redirect
from .models import Form, FormQuestion, FormAnswer
from django.forms import modelformset_factory
from .forms import OISAnswerForm

def form_questions_view(request, form_id):
    # Get the form and its questions
    form_instance = get_object_or_404(Form, id=form_id)
    questions = form_instance.questions.all()

    # Prepare formset for submitting answers
    AnswerFormSet = modelformset_factory(FormAnswer, form=OISAnswerForm, extra=len(questions))

    # Prepare initial data for each question
    initial_data = [{'question': question} for question in questions]

    error_message = None  # Initialize error message variable

    if request.method == 'POST':
        operator_number = request.POST.get('operator_number')
        if not operator_number:
            error_message = "Operator number is required."
            formset = AnswerFormSet(request.POST)
        else:
            # Initialize formset with the posted data
            formset = AnswerFormSet(request.POST)
            if formset.is_valid():
                for i, form in enumerate(formset):
                    answer_data = form.cleaned_data.get('answer')
                    if answer_data:
                        # Get the corresponding question
                        question = questions[i]

                        # Create a new answer object including the operator number
                        FormAnswer.objects.create(
                            question=question,
                            answer=answer_data,
                            operator_number=operator_number
                        )
                return redirect('form_questions', form_id=form_instance.id)
            else:
                error_message = "There was an error with your submission. Please check your answers."
    else:
        formset = AnswerFormSet(queryset=FormAnswer.objects.none(), initial=initial_data)

    # Zip the questions and formset forms
    question_form_pairs = zip(questions, formset.forms)

    return render(request, 'forms/form_questions.html', {
        'form_instance': form_instance,
        'question_form_pairs': question_form_pairs,
        'formset': formset,
        'error_message': error_message,
    })




from django.shortcuts import render, get_object_or_404
from .models import Form
from collections import defaultdict
import pprint

def view_records(request, form_id):
    # Fetch the form instance and its questions
    form_instance = get_object_or_404(Form, id=form_id)
    questions = form_instance.questions.all()

    # Initialize a list for timestamps and the final data structure for table rows
    submission_timestamps = []
    submission_data = []

    # Collect unique timestamps and organize answers by feature
    answers_by_timestamp = defaultdict(lambda: defaultdict(lambda: None))
    for question in questions:
        for answer in question.answers.order_by("created_at"):
            timestamp_str = answer.created_at.strftime("%Y-%m-%d %H:%M:%S")
            
            # Track unique submission timestamps in order of creation
            if timestamp_str not in submission_timestamps:
                submission_timestamps.append(timestamp_str)
            
            # Map answer by question and timestamp
            answers_by_timestamp[question.id][timestamp_str] = {
                "answer": answer.answer,
                "created_at": answer.created_at
            }

    # Reverse sort submission timestamps to display latest submissions first
    submission_timestamps.sort(reverse=True)

    # Prepare each question record for display
    for question in questions:
        row_data = {
            "feature": question.question.get("feature", "N/A"),
            "characteristic": question.question.get("characteristic", "N/A"),
            "answers": []
        }

        # Fill in answers for each submission timestamp, aligned with the correct column
        for timestamp in submission_timestamps:
            if timestamp in answers_by_timestamp[question.id]:
                answer_data = answers_by_timestamp[question.id][timestamp]
                row_data["answers"].append({
                    "answer": answer_data["answer"],
                    "created_at": answer_data["created_at"]
                })
            else:
                row_data["answers"].append(None)  # No answer for this timestamp

        submission_data.append(row_data)

    # Debug output
    pprint.pprint(submission_data)

    return render(request, 'forms/view_records.html', {
        "form_instance": form_instance,
        "submission_timestamps": submission_timestamps,
        "submission_data": submission_data,
    })



