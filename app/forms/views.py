from django.shortcuts import render, redirect, get_object_or_404
from .forms import FORM_TYPE_FORMS, OISQuestionForm
from .models import FormType, Form, FormQuestion
from django.forms import modelformset_factory
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.db.models import Q




def index(request):
    # Check if the user is logged in and belongs to the LPA Managers group
    is_lpa_manager = request.user.is_authenticated and request.user.groups.filter(name="LPA Managers").exists()

    return render(request, 'forms/index.html', {'is_lpa_manager': is_lpa_manager})


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
from django.contrib.auth.models import Group

def find_forms_view(request):
    # Get the form type ID from the request
    form_type_id = request.GET.get('form_type')

    if form_type_id:
        # Fetch the FormType object
        form_type = get_object_or_404(FormType, id=form_type_id)
        
        # Fetch the forms of that form type, ordering by created_at descending
        forms = Form.objects.filter(form_type_id=form_type_id).order_by('-created_at')
        
        # Gather all unique metadata keys across all forms for this form type
        metadata_keys = set()
        for form in forms:
            metadata_keys.update(form.metadata.keys())  # Assuming `metadata` is a dictionary

        # Check if the user is authenticated and part of the "LPA Managers" group
        is_lpa_manager = False
        if request.user.is_authenticated:
            is_lpa_manager = request.user.groups.filter(name="LPA Managers").exists()

        is_quality_engineer = False
        if request.user.is_authenticated:
            is_quality_engineer = request.user.groups.filter(name="Quality Engineer").exists()


        return render(request, 'forms/find_forms.html', {
            'form_type': form_type,
            'forms': forms,
            'metadata_keys': metadata_keys,
            'is_lpa_manager': is_lpa_manager,  # Pass this to the template
            'is_quality_engineer': is_quality_engineer,
        })

    # If no form type is selected, display the form type selection
    form_types = FormType.objects.all()

    # Check if the user is authenticated and part of the "LPA Managers" group
    is_lpa_manager = False
    if request.user.is_authenticated:
        is_lpa_manager = request.user.groups.filter(name="LPA Managers").exists()

    is_quality_engineer = False
    if request.user.is_authenticated:
        is_quality_engineer = request.user.groups.filter(name="Quality Engineer").exists()

    return render(request, 'forms/select_form_type.html', {
        'form_types': form_types,
        'is_lpa_manager': is_lpa_manager,  # Pass this to the template
        'is_quality_engineer': is_quality_engineer,  # Pass this to the template

    })













# ==============================================================================
# ==============================================================================
# ======================== Bulk insert tool ====================================
# ==============================================================================
# ==============================================================================


from django.shortcuts import render, redirect
from .models import Form, FormQuestion, FormType
import json

def bulk_form_and_question_create_view(request):
    if request.method == 'POST':
        data_json = request.POST.get('data_json')
        delete_existing = request.POST.get('delete_existing') == 'on'

        try:
            data = json.loads(data_json)
        except json.JSONDecodeError as e:
            return render(request, 'forms/bulk_question_create.html', {
                'error': f'Invalid JSON data: {e}',
                'data_json': data_json,
            })

        form_data = data.get('form')
        questions_data = data.get('questions', [])

        # Create the new OIS Form
        form_instance = Form(
            name=form_data.get('name'),
            form_type=FormType.objects.get(name="OIS"),
            metadata={
                'part_number': form_data.get('part_number'),
                'operation': form_data.get('operation'),
                'part_name': form_data.get('part_name'),
                'year': form_data.get('year'),
                'mod_level': form_data.get('mod_level'),
                'machine': form_data.get('machine'),
                'mod_date': form_data.get('mod_date')
            }
        )
        form_instance.save()

        # Optionally delete existing questions if specified
        if delete_existing:
            form_instance.questions.all().delete()

        # Create questions associated with this form
        for index, question_data in enumerate(questions_data, start=1):
            question_data['order'] = question_data.get('order', index)
            FormQuestion.objects.create(
                form=form_instance,
                question=question_data
            )

        return redirect('form_edit', form_id=form_instance.id)

    else:
        return render(request, 'forms/bulk_question_create.html')





# {
#     "form": {
#         "name": "Sample OIS Form",
#         "part_number": "PN123",
#         "operation": "Op456",
#         "part_name": "Sample Part",
#         "year": "2023",
#         "mod_level": "A1",
#         "machine": "Machine XYZ",
#         "mod_date": "2023-11-11"
#     },
#     "questions": [
#         {
#             "feature": "67",
#             "special_characteristic": "Bu",
#             "characteristic": "Hub OD (Air Gauge)",
#             "specifications": "Ø30.187 - Ø30.213 mm",
#             "sample_frequency": "100%",
#             "sample_size": "100%",
#             "done_by": "OP/QA",
#             "checkmark": true
#         },
#         {
#             "feature": "HP",
#             "special_characteristic": "D",
#             "characteristic": "Hole(s) Presence (Visual/Gauge)",
#             "specifications": "Present YES / NO",
#             "sample_frequency": "100%",
#             "sample_size": "100%",
#             "done_by": "OP / QA",
#             "checkmark": false
#         }
#         // Add more questions as needed...
#     ]
# }








        




# ==================================================================
# ==================================================================
# ================= Operator Form Template OIS =====================
# ==================================================================
# ==================================================================

from django.shortcuts import render, get_object_or_404, redirect
from django.forms import modelformset_factory
from .models import Form, FormQuestion, FormAnswer
from .forms import OISAnswerForm, LPAAnswerForm
import datetime
import json

def form_questions_view(request, form_id):
    # Get the form instance and its form type
    form_instance = get_object_or_404(Form, id=form_id)
    form_type = form_instance.form_type

    # Debug print to check form instance and type
    print(f"[DEBUG] Form instance: {form_instance}, Form type: {form_type}")

    # Determine the template to render based on the form type's template name
    template_name = f'forms/{form_type.template_name}'

    # Map form types to their respective form classes
    answer_form_classes = {
        'OIS': OISAnswerForm,
        'LPA': LPAAnswerForm,
        # Add more form types as needed
    }

    # Get the form class for the current form type
    answer_form_class = answer_form_classes.get(form_type.name)
    if not answer_form_class:
        raise ValueError(f"No form class defined for form type: {form_type.name}")

    # Debug print to check selected form class
    # print(f"[DEBUG] Selected form class: {answer_form_class}")

    # Sort questions by the "order" key in the question JSON field directly
    questions = sorted(
        form_instance.questions.all(),
        key=lambda q: q.question.get("order", 0)  # Access the 'order' directly from the dictionary
    )

    # Debug print to check the number of questions
    # print(f"[DEBUG] Number of questions: {len(questions)}")

    # Prepare formset for submitting answers, initializing with the number of questions
    AnswerFormSet = modelformset_factory(FormAnswer, form=answer_form_class, extra=len(questions))

    # Prepare initial data for each question
    initial_data = [{'question': question} for question in questions]

    error_message = None  # Initialize error message variable

    # Retrieve the operator number from cookies
    operator_number = request.COOKIES.get('operator_number', '')

    # Debug print to check operator number
    # print(f"[DEBUG] Operator number from cookies: {operator_number}")

    if request.method == 'POST':
        operator_number = request.POST.get('operator_number')

        # Debug print to check operator number from POST
        # print(f"[DEBUG] Operator number from POST: {operator_number}")

        if not operator_number:
            error_message = "Operator number is required."
            formset = AnswerFormSet(
                request.POST, 
                queryset=FormAnswer.objects.none(), 
                form_kwargs={'user': request.user}  # Pass user to forms
            )
        else:
            # Set the operator number as a cookie to persist it
            response = redirect('form_questions', form_id=form_instance.id)
            response.set_cookie('operator_number', operator_number, expires=datetime.datetime.now() + datetime.timedelta(days=365))

            # Initialize formset with the posted data and pass the user
            formset = AnswerFormSet(
                request.POST, 
                queryset=FormAnswer.objects.none(), 
                form_kwargs={'user': request.user}  # Pass user during POST
            )

            # Debug print to check if user is being passed to the formset
            # print(f"[DEBUG] User passed to formset during POST: {request.user}")

            if formset.is_valid():
                for i, form in enumerate(formset):
                    answer_data = form.cleaned_data.get('answer')
                    if answer_data:
                        # Get the corresponding question
                        question = questions[i]

                        # Debug print to check answer data and operator number
                        # print(f"[DEBUG] Answer data: {answer_data}, Operator number: {operator_number}")

                        # Create a new answer object including the operator number
                        FormAnswer.objects.create(
                            question=question,
                            answer=answer_data,
                            operator_number=operator_number  # Store the operator number
                        )
                return response
            else:
                error_message = "There was an error with your submission. Please check your answers."
    else:
        # Generate a formset with initial data, setting up the answer options based on checkmark
        formset = AnswerFormSet(
            queryset=FormAnswer.objects.none(), 
            initial=initial_data, 
            form_kwargs={'user': request.user}  # Pass user during GET
        )

        # Debug print to verify user is being passed during initialization
        # print(f"[DEBUG] User passed to formset initialization: {request.user}")

        for form, question in zip(formset.forms, questions):
            form.__init__(question=question)  # Pass question to form for conditional field handling

    # Zip the questions and formset forms for paired rendering
    question_form_pairs = zip(questions, formset.forms)

    # Render the template
    return render(request, template_name, {
        'form_instance': form_instance,
        'question_form_pairs': question_form_pairs,
        'formset': formset,
        'error_message': error_message,
        'operator_number': operator_number,  # Pass the operator number to the template
    })




from django.shortcuts import render, get_object_or_404
from .models import Form
from collections import defaultdict
import pprint
from datetime import timedelta

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
            # Convert UTC datetime to EST by subtracting 5 hours
            utc_timestamp = answer.created_at
            est_timestamp = utc_timestamp - timedelta(hours=5)  # UTC to EST (UTC - 5)

            # Format the EST timestamp to "YYYY-MM-DD HH:MM"
            timestamp_str = est_timestamp.strftime("%Y-%m-%d %H:%M")

            # Track unique submission timestamps in order of creation
            if timestamp_str not in submission_timestamps:
                submission_timestamps.append(timestamp_str)
            
            # Map answer by question and timestamp
            answers_by_timestamp[question.id][timestamp_str] = {
                "answer": answer.answer,
                "created_at": est_timestamp,
            }

    # Reverse sort submission timestamps to display latest submissions first
    submission_timestamps.sort(reverse=True)

    # Limit to the 10 most recent timestamps
    submission_timestamps = submission_timestamps[:48]

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
                    "created_at": answer_data["created_at"],
                    "blank": False  # Not blank if there's an answer
                })
            else:
                # Mark missing answers as blank
                row_data["answers"].append({"blank": True})

        submission_data.append(row_data)

    return render(request, 'forms/view_records.html', {
        "form_instance": form_instance,
        "submission_timestamps": submission_timestamps,
        "submission_data": submission_data,
    })





def form_by_metadata_view(request):
    # Extract query parameters
    form_type_id = request.GET.get('formtype')
    operation = request.GET.get('operation')
    part_number = request.GET.get('part_number')

    # Validate that the necessary query parameters are provided
    if not form_type_id or not operation or not part_number:
        return render(request, 'forms/error.html', {
            'message': 'Missing query parameters. Please provide formtype, operation, and part_number.'
        })

    # Search for the form matching the given criteria
    try:
        form_instance = Form.objects.get(
            form_type_id=form_type_id,
            metadata__operation=operation,
            metadata__part_number=part_number
        )
    except Form.DoesNotExist:
        return render(request, 'forms/error.html', {
            'message': 'No form found matching the provided criteria.'
        })

    # Fetch the form type and determine the template to use
    form_type = form_instance.form_type
    template_name = f'forms/{form_type.template_name}'

    # Map form types to their respective answer form classes
    answer_form_classes = {
        'OIS': OISAnswerForm,
        'LPA': LPAAnswerForm,
    }
    answer_form_class = answer_form_classes.get(form_type.name)

    if not answer_form_class:
        raise ValueError(f"No form class defined for form type: {form_type.name}")

    # Fetch and sort questions based on the "order" field in the question JSON
    questions = sorted(
        form_instance.questions.all(),
        key=lambda q: q.question.get("order", 0)
    )

    # Prepare the formset for answers
    AnswerFormSet = modelformset_factory(FormAnswer, form=answer_form_class, extra=len(questions))
    initial_data = [{'question': question} for question in questions]

    error_message = None
    operator_number = request.COOKIES.get('operator_number', '')

    if request.method == 'POST':
        operator_number = request.POST.get('operator_number')
        machine = request.POST.get('machine', '')  # Get the machine value from POST data

        # Pass the user and machine to form_kwargs
        formset = AnswerFormSet(
            request.POST,
            queryset=FormAnswer.objects.none(),
            form_kwargs={'user': request.user, 'machine': machine}  # Pass the machine here
        )

        if not operator_number:
            error_message = "Operator number is required."
        else:
            if formset.is_valid():
                for i, form in enumerate(formset):
                    answer_data = form.cleaned_data.get('answer')
                    if answer_data:
                        # Create a new answer object including the operator number
                        FormAnswer.objects.create(
                            question=questions[i],
                            answer=answer_data,  # The answer JSON already includes the machine value
                            operator_number=operator_number
                        )
                # Redirect to the same view to clear the form
                return redirect(f"{request.path}?formtype={form_type_id}&operation={operation}&part_number={part_number}")
            else:
                error_message = "There was an error with your submission."
    else:
        # GET request, build formset with initial data, pass the user and machine
        machine = request.POST.get('machine', '')  # Get the machine value from POST data
        formset = AnswerFormSet(
            queryset=FormAnswer.objects.none(),
            initial=initial_data,
            form_kwargs={'user': request.user, 'machine': machine}  # Pass the machine here
        )

    # Zip questions and forms for paired rendering
    question_form_pairs = zip(questions, formset.forms)

    # Render the form view
    return render(request, template_name, {
        'form_instance': form_instance,
        'question_form_pairs': question_form_pairs,
        'formset': formset,
        'error_message': error_message,
        'operator_number': operator_number,
    })

from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from .models import Form

def smart_form_redirect_view(request, form_id):
    form_instance = get_object_or_404(Form, id=form_id)
    
    form_type_id = form_instance.form_type_id
    operation = form_instance.metadata.get('operation')
    part_number = form_instance.metadata.get('part_number')
    
    # Only attempt metadata-based redirect if we have both operation & part_number
    if operation and part_number:
        # Check if a matching Form actually exists. If it does, we redirect to metadata‐based URL
        try:
            Form.objects.get(
                form_type_id=form_type_id,
                metadata__operation=operation,
                metadata__part_number=part_number
            )
            # If we get here, a valid Form with that metadata exists
            querystring = f"?formtype={form_type_id}&operation={operation}&part_number={part_number}"
            return redirect(reverse('form_by_metadata') + querystring)
        except Form.DoesNotExist:
            pass
    
    # Fallback to the ID-based URL
    return redirect('form_questions', form_id=form_id)




def lpa_closeout_view(request):
    from datetime import datetime
    if request.method == 'POST':
        # Process closeout submission
        answer_id = request.POST.get('answer_id')
        closeout_notes = request.POST.get('closeout_notes', '')
        closeout_date = request.POST.get('closeout_date', '')

        # Validate closeout_date
        try:
            closeout_date_parsed = datetime.strptime(closeout_date, '%Y-%m-%d') if closeout_date else None
        except ValueError:
            closeout_date_parsed = None

        if not closeout_date_parsed:
            return redirect('lpa_closeout')  # Invalid date, just refresh for now

        # Fetch the answer and update the JSON field
        try:
            answer = FormAnswer.objects.get(id=answer_id)
            updated_answer = answer.answer.copy()  # Create a copy of the JSON field
            updated_answer['closed_out'] = True
            updated_answer['closeout_date'] = closeout_date_parsed.strftime('%Y-%m-%d')  # Store the date
            if closeout_notes:
                updated_answer['closeout_notes'] = closeout_notes
            answer.answer = updated_answer
            answer.save()
        except FormAnswer.DoesNotExist:
            pass  # Handle gracefully if answer is missing

        return redirect('lpa_closeout')  # Redirect to refresh the page

    # Filter answers where closed_out != true and answer is "No"
    lpa_answers = FormAnswer.objects.filter(
        Q(answer__contains={'answer': 'No'}) & ~Q(answer__contains={'closed_out': True}),
        question__form__form_type__id=15
    ).select_related('question__form__form_type')

    # Debug: Print data to check the backend response
    print("DEBUG: Fetched answers:")
    for answer in lpa_answers:
        print(
            f"Answer ID: {answer.id}, Question ID: {answer.question.id}, "
            f"Question Text: {answer.question.question.get('question_text', 'N/A')}, "
            f"Form Name: {answer.question.form.name}, Answer Data: {answer.answer}"
        )

    # Pass the filtered answers to the template
    context = {
        'lpa_answers': lpa_answers
    }
    return render(request, 'forms/lpa_closeout.html', context)



def closed_lpas_view(request):
    from datetime import datetime
    if request.method == 'POST':
        # Handle editing closeout notes and date
        answer_id = request.POST.get('answer_id')
        closeout_notes = request.POST.get('closeout_notes', '')
        closeout_date = request.POST.get('closeout_date', '')

        # Validate closeout_date
        try:
            closeout_date_parsed = datetime.strptime(closeout_date, '%Y-%m-%d') if closeout_date else None
        except ValueError:
            closeout_date_parsed = None

        if not closeout_date_parsed:
            return redirect('closed_lpas')  # Invalid date, refresh for now

        # Fetch the answer and update the JSON field
        try:
            answer = FormAnswer.objects.get(id=answer_id)
            updated_answer = answer.answer.copy()  # Create a copy of the JSON field
            updated_answer['closeout_date'] = closeout_date_parsed.strftime('%Y-%m-%d')
            updated_answer['closeout_notes'] = closeout_notes
            answer.answer = updated_answer
            answer.save()
        except FormAnswer.DoesNotExist:
            pass  # Handle gracefully if answer is missing

        return redirect('closed_lpas')  # Redirect to refresh the page

    # Fetch answers where closed_out = true
    closed_answers = FormAnswer.objects.filter(
        answer__contains={'closed_out': True},
        question__form__form_type__id=15
    ).select_related('question__form__form_type')

    # Debugging output
    print("DEBUG: Closed LPAs fetched:")
    for answer in closed_answers:
        print(
            f"Answer ID: {answer.id}, Question ID: {answer.question.id}, "
            f"Closeout Date: {answer.answer.get('closeout_date', 'N/A')}, "
            f"Closeout Notes: {answer.answer.get('closeout_notes', 'N/A')}, "
            f"Form Name: {answer.question.form.name}"
        )

    context = {
        'closed_answers': closed_answers
    }
    return render(request, 'forms/closed_lpas.html', context)