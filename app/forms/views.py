from django.shortcuts import render, redirect, get_object_or_404
from .forms import FORM_TYPE_FORMS, OISQuestionForm
from .models import FormType, Form, FormQuestion
from django.forms import modelformset_factory
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.db.models import Q
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from .models import Form
from django.views.decorators.http import require_http_methods
from .forms import FORM_TYPE_FORMS, QUESTION_FORM_CLASSES
from .models import FormType, Form, FormQuestion
from django.forms import modelformset_factory
from django.shortcuts import render, get_object_or_404
from .models import Form, FormType
from django.contrib.auth.models import Group
from django.utils.timezone import now
import datetime
from django.shortcuts import render, redirect
from .models import Form, FormQuestion, FormType
import json
from django.forms import modelformset_factory
from .models import Form, FormQuestion, FormAnswer
from .forms import OISAnswerForm, LPAAnswerForm
import datetime
import json
from django.utils import timezone
from .models import Form
from collections import defaultdict
import pprint
from datetime import timedelta
from django.urls import reverse
from .models import Form
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.template.loader import render_to_string
from .forms import LPAQuestionForm
from django.http import JsonResponse
from .models import Form
from django.utils import timezone
from datetime import timedelta, datetime
from collections import OrderedDict
import pytz
from .emailer import send_hybrid_email  # Import the function from emailer.py




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
                queryset=form_instance.questions.filter(
                    ~Q(question__has_key='expired') | Q(question__expired=False)  # Exclude expired questions
                ).order_by('question__order') if form_instance else FormQuestion.objects.none()
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
            # Fetch questions ordered by the 'order' field in the JSON, excluding expired
            form = form_class(instance=form_instance)
            question_formset = QuestionFormSet(
                queryset=form_instance.questions.filter(
                    ~Q(question__has_key='expired') | Q(question__expired=False)  # Exclude expired questions
                ).order_by('question__order') if form_instance else FormQuestion.objects.none()
            )

        # Pass `form_instance` to the template
        return render(request, 'forms/form_create.html', {
            'form': form,
            'question_formset': question_formset,
            'form_type': form_type,
            'original_form': form_instance,  # Ensure this is passed to the template
        })

    # If no form_type is provided, show a page to select the form type
    form_types = FormType.objects.all()
    return render(request, 'forms/select_form_type.html', {'form_types': form_types})









# =============================================================================
# =============================================================================
# ======================= Find forms Now ======================================
# =============================================================================
# =============================================================================



def find_and_tag_expired_questions():
    """
    Finds and tags all expired questions based on their expiry_date field.
    """
    # Get the current date
    today = now().date()

    # Fetch all questions from the FormQuestion model
    questions = FormQuestion.objects.all()

    for question in questions:
        # Extract the JSON object
        question_data = question.question

        # Check if the expiry_date key exists in the JSON and is valid
        expiry_date_str = question_data.get('expiry_date')
        if expiry_date_str:
            try:
                # Parse the expiry_date from the JSON object
                expiry_date = datetime.strptime(expiry_date_str, '%Y-%m-%d').date()
                if expiry_date < today:
                    # Tag the question as expired if the date is in the past
                    question_data['expired'] = True
                else:
                    # Ensure the expired key is False if the expiry_date is valid and not expired
                    question_data['expired'] = False
            except ValueError:
                # If the expiry_date is invalid, skip this question
                continue

            # Save the updated question data back to the model
            question.question = question_data
            question.save()


def find_deleted_forms(form_type_id):
    """
    Find and return the IDs of all forms for the specified form type
    that have 'deleted: true' in their metadata.
    """
    # Fetch all forms for the given form type that are marked as deleted
    deleted_forms = Form.objects.filter(
        form_type_id=form_type_id,
        metadata__deleted=True  # Filter forms with 'deleted: true' in metadata
    )

    # Collect the IDs of the deleted forms
    deleted_form_ids = [form.id for form in deleted_forms]
    print(f"[INFO] Deleted forms for form type {form_type_id}: {deleted_form_ids}")

    # Return the list of deleted form IDs
    return deleted_form_ids



def find_forms_view(request):

    # Check and tag expired questions
    find_and_tag_expired_questions()

    # Get the form type ID from the request
    form_type_id = request.GET.get('form_type')

    if form_type_id:
        # Fetch the FormType object
        form_type = get_object_or_404(FormType, id=form_type_id)
        
        # Get the IDs of deleted forms
        deleted_form_ids = find_deleted_forms(form_type_id)

        # Fetch the forms of that form type, excluding deleted forms and ordering by created_at descending
        forms = Form.objects.filter(
            form_type_id=form_type_id
        ).exclude(id__in=deleted_form_ids).order_by('-created_at')
        
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
            'is_authenticated': request.user.is_authenticated,  # Add this

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
        'is_authenticated': request.user.is_authenticated,  # Add this
    })













# ==============================================================================
# ==============================================================================
# ======================== Bulk insert tool ====================================
# ==============================================================================
# ==============================================================================



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



def print_out_of_spec_answers(answers):
    """
    Checks submitted answers for out-of-range values and prints relevant information.
    - Only prints out-of-spec answers.
    - Displays: Answer, Question ID, Form ID, Part Number, Machine, and Operation.
    """
    print("\n--- Out-of-Range Answers ---")

    for answer in answers:
        question = answer['question']
        answer_value = answer['answer']
        input_type = answer['type']

        # Only check range if it's a text input (not pass/fail)
        if input_type != 'text':
            continue

        # Check if the question is range-based
        is_range_based = question.question.get('specification_type', 'N/A') == 'range'
        
        if not is_range_based:
            continue

        # Get min and max values from the specifications
        specifications = question.question.get('specifications', {})
        min_value = specifications.get('min', None)
        max_value = specifications.get('max', None)

        # Convert to float if possible
        try:
            min_value = float(min_value)
            max_value = float(max_value)
            answer_float = float(answer_value)
        except (TypeError, ValueError):
            continue
        
        # Check if the answer is out of range
        out_of_range = False
        if min_value is not None and answer_float < min_value:
            status = "Below Minimum"
            out_of_range = True
        elif max_value is not None and answer_float > max_value:
            status = "Above Maximum"
            out_of_range = True
        
        if out_of_range:
            # Get Question ID and Form ID
            question_id = question.id
            form_id = question.form.id

            # Get the form's metadata
            form_metadata = question.form.metadata
            part_number = form_metadata.get('part_number', 'N/A')
            machine = form_metadata.get('machine', 'N/A')
            operation = form_metadata.get('operation', 'N/A')

            # Print the out-of-spec details
            print(f"[Out of Spec] Answer: {answer_value} | Question ID: {question_id} | Form ID: {form_id}")
            print(f"               Part Number: {part_number} | Machine: {machine} | Operation: {operation}")
            print("------------------------------------------------------------")

    print("--- End of Out-of-Range Check ---\n")





def submit_ois_answers(formset, request, questions):
    # Capture the inspection type and operator number
    inspection_type = request.POST.get('inspection_type', 'OIS')
    operator_number = request.POST.get('operator_number', '')

    print("\n--- Collecting OIS Answers ---")

    # Loop through each question to collect its answers
    all_answers = []
    for i, question in enumerate(questions):
        # Safely convert sample_size to an integer or default to 1
        sample_size_value = question.question.get("sample_size", 1)
        sample_size = int(sample_size_value) if str(sample_size_value).isdigit() else 1
        
        answers = []

        # Check if the question uses a checkmark (Pass/Fail)
        is_checkmark = question.question.get('checkmark', False)
        
        # Collect answers based on the input type
        if is_checkmark:
            # Pass/Fail Dropdown
            answer_key = f"answer_{question.id}"
            answer_data = request.POST.get(answer_key)
            if answer_data:
                answers.append({
                    'answer': answer_data,
                    'type': 'pass_fail'
                })
        else:
            # Text Input for Sample Size
            for j in range(sample_size):
                answer_key = f"answer_{question.id}_{j}"
                answer_data = request.POST.get(answer_key)
                if answer_data:
                    answers.append({
                        'answer': answer_data,
                        'type': 'text'
                    })

        # Save each answer as a separate FormAnswer entry
        for answer in answers:
            # Format the answer JSON for the entry
            answer_json = {
                'answer': answer['answer'],
                'input_type': answer['type'],
                'inspection_type': inspection_type
            }

            # Save each answer as a separate FormAnswer entry
            FormAnswer.objects.create(
                question=question,
                answer=answer_json,  # Save as JSON for easier processing later
                operator_number=operator_number,
                created_at=timezone.now()
            )

            # Add to the all_answers list for post-submission checks
            all_answers.append({
                'question': question,
                'answer': answer['answer'],
                'type': answer['type']
            })

    print("\n--- All Answers Saved Successfully ---")

    # === Call the new out-of-range checker ===
    print_out_of_spec_answers(all_answers)







# Function to format specifications more naturally
def format_specifications(spec):
    """
    Formats the specifications field to attach units directly to each value.
    """
    if isinstance(spec, dict):
        # Extract units if present
        units = spec.get('units', '')
        
        # Build the formatted string with units attached to each value
        formatted_parts = []
        for key, value in spec.items():
            if key != 'units':  # Skip units itself
                # Attach units to each relevant value
                formatted_value = f"{value} {units}" if units else f"{value}"
                formatted_parts.append(f"{key.capitalize()}: {formatted_value}")
        
        return ", ".join(formatted_parts)
    
    try:
        # Try to parse as JSON if it's a string
        spec_dict = json.loads(spec)
        if isinstance(spec_dict, dict):
            # Repeat the same logic if it was a JSON string
            units = spec_dict.get('units', '')
            formatted_parts = []
            for key, value in spec_dict.items():
                if key != 'units':
                    formatted_value = f"{value} {units}" if units else f"{value}"
                    formatted_parts.append(f"{key.capitalize()}: {formatted_value}")
            return ", ".join(formatted_parts)
    except (json.JSONDecodeError, TypeError):
        pass
    
    return spec  # Return as-is if not JSON


def populate_answers_with_range_check(questions_dict, answers, date_hour_range, est):
    """
    Populate all answers into the corresponding date-hour slots and check for range-based answers.
    """
    for question_key, question_data in questions_dict.items():
        # Filter the answers once per question to avoid redundant checks
        question_answers = [
            answer for answer in answers
            if answer.question.question.get('feature', 'N/A') in question_key and
               answer.question.question.get('characteristic', 'N/A') in question_key
        ]

        # Check if the question is range-based (only once per question)
        is_range_based = (
            question_answers and 
            question_answers[0].question.question.get('specification_type', 'N/A') == 'range'
        )
        
        # If range-based, get the min and max values
        if is_range_based:
            specifications = question_answers[0].question.question.get('specifications', {})
            min_value = specifications.get('min', None)
            max_value = specifications.get('max', None)
            
            # Convert to float if possible
            try:
                min_value = float(min_value)
                max_value = float(max_value)
            except (TypeError, ValueError):
                min_value = None
                max_value = None

        for date_hour in date_hour_range:
            # Get all answers for the question on this date-hour
            hourly_answers = [
                answer.answer.get('answer', '')
                for answer in question_answers
                if answer.created_at.astimezone(est).strftime('%Y-%m-%d %H:00') == date_hour
            ]

            tagged_answers = []  # Collect tagged answers for this date-hour

            # Only process if it's a range-based question
            if is_range_based and hourly_answers:
                for ans in hourly_answers:
                    try:
                        ans_float = float(ans)  # Convert answer to float for comparison
                        
                        # Check if the answer is out of range
                        if min_value is not None and ans_float < min_value:
                            status = "Out of Range (Below Min)"
                            tagged_answers.append(f'<span class="out-of-range">{ans}</span>')
                        elif max_value is not None and ans_float > max_value:
                            status = "Out of Range (Above Max)"
                            tagged_answers.append(f'<span class="out-of-range">{ans}</span>')
                        else:
                            status = "In Range"
                            tagged_answers.append(ans)
                    
                    except ValueError:
                        tagged_answers.append(f'<span class="invalid-answer">{ans}</span>')

            else:
                # If not range-based or no answers, keep it normal
                tagged_answers = hourly_answers

            # Format the answers for this date-hour as a comma-separated string
            if tagged_answers:
                formatted_answers = ", ".join(tagged_answers)
            else:
                formatted_answers = "-"  # Use "-" if no answers for this date-hour

            # Append the formatted string for this date-hour
            question_data['Answers'].append(formatted_answers)





# Main function to get seven day answers
def seven_day_answers(form_instance):
    """
    Fetch and organize all answers for all questions in this form ID for the last 7 days,
    with Date and Hour as column headers (without the year) and Questions as row headers.
    Newest dates and hours on the left, showing all answers for each hour up until the current hour.
    """
    # EST timezone setup
    est = pytz.timezone('America/New_York')

    # Get the current time in EST
    current_time = timezone.now().astimezone(est)
    current_hour = current_time.replace(minute=0, second=0, microsecond=0)
    
    # Generate the hourly range for the last 7 days up to the current hour
    date_hour_range = []
    for i in range(7 * 24):
        hour = current_hour - timedelta(hours=i)
        
        # Remove the year from the header (MM-DD HH:00)
        date_hour_range.append(hour.strftime('%m-%d %H:00'))

    date_hour_range.sort(reverse=True)  # Newest hour on the left

    # Fetch all answers for all questions in this form for the last 7 days
    answers = (
        FormAnswer.objects
        .filter(
            question__form=form_instance,
            created_at__gte=(current_hour - timedelta(days=6))
        )
        .select_related('question')
        .order_by('created_at')
    )

    # Organize answers by question and date-hour
    questions_dict = OrderedDict()
    for question in form_instance.questions.all():
        key = f"{question.question.get('feature', 'N/A')} - {question.question.get('characteristic', 'N/A')}"
        sample_size = question.question.get('sample_size', 'N/A')  # Get Sample Size
        
        # Format the specifications using the new function
        formatted_specifications = format_specifications(question.question.get('specifications', 'N/A'))

        questions_dict[key] = {
            'Feature': question.question.get('feature', 'N/A'),
            'Characteristic': question.question.get('characteristic', 'N/A'),
            'Specifications': formatted_specifications,  # Formatted Specifications
            'SampleSize': sample_size,
            'Answers': []  # Store pre-formatted answers as list of strings
        }

    # Call the new function to populate answers and check for range-based questions
    populate_answers_with_range_check(questions_dict, answers, date_hour_range, est)

    return {
        'date_range': date_hour_range,      # Dates and hours for the columns (newest to oldest)
        'questions_dict': questions_dict  # All questions and their pre-formatted answers
    }









def form_questions_view(request, form_id):
    # Get the form instance and its form type
    form_instance = get_object_or_404(Form, id=form_id)
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

    # Sort questions by the "order" key in the question JSON
    questions = sorted(
        form_instance.questions.all(),
        key=lambda q: q.question.get("order", 0)
    )

    # Prepare input ranges for each question based on sample size
    question_input_ranges = []
    for question in questions:
        sample_size_value = question.question.get("sample_size", 1)
        # Check if sample_size is a digit; if not, default to 1
        if str(sample_size_value).isdigit():
            sample_size = int(sample_size_value)
        else:
            sample_size = 1

        input_range = list(range(sample_size))
        question_input_ranges.append({
            'question': question,
            'input_range': input_range
        })

    # Prepare the formset for submitting answers
    AnswerFormSet = modelformset_factory(FormAnswer, form=answer_form_class, extra=len(questions))
    initial_data = [{'question': question} for question in questions]

    error_message = None
    operator_number = request.COOKIES.get('operator_number', '')

    # Only pass 'user' in form_kwargs if the form type requires it.
    USER_REQUIRED_FORM_TYPES = [15]
    form_kwargs = {}
    if form_instance.form_type.id in USER_REQUIRED_FORM_TYPES:
        form_kwargs['user'] = request.user

    if request.method == 'POST':
        operator_number = request.POST.get('operator_number')
        formset = AnswerFormSet(
            request.POST,
            queryset=FormAnswer.objects.none(),
            form_kwargs=form_kwargs  # Conditionally include the user
        )

        if not operator_number:
            error_message = "Operator number is required."
        else:
            if formset.is_valid():
                if form_instance.form_type.name == 'OIS':
                    print("This is ois")
                    submit_ois_answers(formset, request, questions)

                    # Call the new function to get and print 7-day answers
                    seven_day_data = seven_day_answers(form_instance)

                    return render(request, template_name, {
                        'form_instance': form_instance,
                        'question_input_ranges': question_input_ranges,
                        'formset': formset,
                        'error_message': error_message,
                        'operator_number': operator_number,
                        'seven_day_data': seven_day_data  # Add 7-day answers data to context
                    })


                # Create one timestamp to use for all answers
                timestamp = timezone.now()
                for i, form in enumerate(formset):
                    answers = []
                    sample_size = questions[i].question.get("sample_size", 1)
                    for j in range(sample_size):
                        answer_key = f"answer_{questions[i].id}_{j}"
                        answer_data = request.POST.get(answer_key)
                        if answer_data:
                            answers.append(answer_data)
                    
                    for answer in answers:
                        FormAnswer.objects.create(
                            question=questions[i],
                            answer=answer,
                            operator_number=operator_number,
                            created_at=timestamp
                        )
                return redirect('form_questions', form_id=form_instance.id)
            else:
                error_message = "There was an error with your submission. Please check your answers."
    else:
        formset = AnswerFormSet(
            queryset=FormAnswer.objects.none(),
            initial=initial_data,
            form_kwargs=form_kwargs
        )
        for form, question in zip(formset.forms, questions):
            form.__init__(question=question)

    seven_day_data = seven_day_answers(form_instance) if form_instance.form_type.name == 'OIS' else None

    return render(request, template_name, {
        'form_instance': form_instance,
        'question_input_ranges': question_input_ranges,
        'formset': formset,
        'error_message': error_message,
        'operator_number': operator_number,
        'seven_day_data': seven_day_data,
    })







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





# def form_by_metadata_view(request):
#     # Extract query parameters
#     form_type_id = request.GET.get('formtype')
#     operation = request.GET.get('operation')
#     part_number = request.GET.get('part_number')

#     # Validate that the necessary query parameters are provided
#     if not form_type_id or not operation or not part_number:
#         return render(request, 'forms/error.html', {
#             'message': 'Missing query parameters. Please provide formtype, operation, and part_number.'
#         })

#     # Search for the form matching the given criteria
#     form_instance = get_object_or_404(
#         Form,
#         form_type_id=form_type_id,
#         metadata__operation=operation,
#         metadata__part_number=part_number
#     )

#     # Fetch the form type and determine the template to use
#     form_type = form_instance.form_type
#     template_name = f'forms/{form_type.template_name}'

#     # Map form types to their respective answer form classes
#     answer_form_classes = {
#         'OIS': OISAnswerForm,
#         'LPA': LPAAnswerForm,
#     }
#     answer_form_class = answer_form_classes.get(form_type.name)
#     if not answer_form_class:
#         raise ValueError(f"No form class defined for form type: {form_type.name}")

#     # Fetch and sort questions based on the "order" field in the question JSON, excluding expired questions
#     questions = sorted(
#         form_instance.questions.filter(
#             ~Q(question__has_key='expired') | Q(question__expired=False)
#         ),
#         key=lambda q: q.question.get("order", 0)
#     )

#     # Prepare the formset for answers
#     AnswerFormSet = modelformset_factory(FormAnswer, form=answer_form_class, extra=len(questions))
#     initial_data = [{'question': question} for question in questions]

#     error_message = None
#     operator_number = request.COOKIES.get('operator_number', '')

#     if request.method == 'POST':
#         operator_number = request.POST.get('operator_number')
#         machine = request.POST.get('machine', '')  # Get machine value from POST data
#         formset = AnswerFormSet(
#             request.POST,
#             queryset=FormAnswer.objects.none(),
#             form_kwargs={'user': request.user, 'machine': machine}
#         )

#         if not operator_number:
#             error_message = "Operator number is required."
#         else:
#             if formset.is_valid():
#                 # Generate a single timestamp for the entire submission
#                 timestamp = timezone.now()
#                 for i, form in enumerate(formset):
#                     answer_data = form.cleaned_data.get('answer')
#                     if answer_data:
#                         FormAnswer.objects.create(
#                             question=questions[i],
#                             answer=answer_data,
#                             operator_number=operator_number,
#                             created_at=timestamp  # All answers share the same timestamp
#                         )
#                 # Redirect to clear the form after successful submission
#                 return redirect(f"{request.path}?formtype={form_type_id}&operation={operation}&part_number={part_number}")
#             else:
#                 error_message = "There was an error with your submission."
#     else:
#         machine = request.GET.get('machine', '')
#         formset = AnswerFormSet(
#             queryset=FormAnswer.objects.none(),
#             initial=initial_data,
#             form_kwargs={'user': request.user, 'machine': machine}
#         )

#     question_form_pairs = zip(questions, formset.forms)

#     return render(request, template_name, {
#         'form_instance': form_instance,
#         'question_form_pairs': question_form_pairs,
#         'formset': formset,
#         'error_message': error_message,
#         'operator_number': operator_number,
#     })




# This is your consolidated unified view.
# You may want to add this URL pattern (in your urls.py) with optional parameters.
# For example:
#   path('forms/form/<int:form_id>/', unified_form_view, name='unified_form'),
#   path('forms/form/<int:form_id>/<str:operation>/<str:partnumber>/', unified_form_view, name='unified_form'),
@require_http_methods(["GET", "POST"])
def unified_form_view(request, form_id, operation=None, partnumber=None):
    print(f"[DEBUG] Entered unified_form_view with form_id: {form_id}, operation: {operation}, partnumber: {partnumber}")

    # Retrieve the form instance
    form_instance = get_object_or_404(Form, id=form_id)
    form_type = form_instance.form_type
    print(f"[DEBUG] Retrieved form: {form_instance} (Type: {form_type.name})")

    # Extract metadata values (if they exist)
    metadata_operation = form_instance.metadata.get('operation')
    metadata_part_number = form_instance.metadata.get('part_number')
    print(f"[DEBUG] Form metadata - operation: {metadata_operation}, part_number: {metadata_part_number}")

    if metadata_operation and metadata_part_number:
        # Create slug versions by replacing spaces with underscores
        expected_operation_slug = metadata_operation.replace(" ", "_")
        expected_partnumber_slug = metadata_part_number.replace(" ", "_")
        print(f"[DEBUG] Expected slug values - operation: {expected_operation_slug}, partnumber: {expected_partnumber_slug}")

        # If the URL does not include the slugs or they don't match, redirect to the correct URL.
        if operation != expected_operation_slug or partnumber != expected_partnumber_slug:
            print("[DEBUG] URL slug mismatch or missing. Redirecting to the URL with correct slug values.")
            new_url = reverse('unified_form', kwargs={
                'form_id': form_id,
                'operation': expected_operation_slug,
                'partnumber': expected_partnumber_slug
            })
            print(f"[DEBUG] Redirect URL: {new_url}")
            return redirect(new_url)
        else:
            print("[DEBUG] URL slug matches metadata. Proceeding to render the form view.")
    else:
        print("[DEBUG] Metadata missing operation and/or part_number. Falling back to using form_id only.")

    # At this point, we can use the same logic as your form_questions_view
    # (or merge that logic here). In this example we delegate to form_questions_view.
    print("[DEBUG] Rendering form_questions_view for form_id:", form_id)
    return form_questions_view(request, form_id=form_id)



# def smart_form_redirect_view(request, form_id):
#     form_instance = get_object_or_404(Form, id=form_id)
    
#     form_type_id = form_instance.form_type_id
#     operation = form_instance.metadata.get('operation')
#     part_number = form_instance.metadata.get('part_number')
    
#     # Only attempt metadata-based redirect if we have both operation & part_number
#     if operation and part_number:
#         try:
#             # Try to get the unique matching form by metadata
#             Form.objects.get(
#                 form_type_id=form_type_id,
#                 metadata__operation=operation,
#                 metadata__part_number=part_number
#             )
#             # If we get here, exactly one form exists, so build the query string
#             querystring = f"?formtype={form_type_id}&operation={operation}&part_number={part_number}"
#             return redirect(reverse('form_by_metadata') + querystring)
#         except Form.DoesNotExist:
#             # If no matching form is found, fall through to the fallback URL
#             pass
#         except Form.MultipleObjectsReturned:
#             # If multiple forms match the metadata, gracefully fall back to the ID-based URL
#             return redirect('form_questions', form_id=form_id)
    
#     # Fallback to the ID-based URL
#     return redirect('form_questions', form_id=form_id)





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





def create_form_copy_view(request, form_id):
    """
    View to create a copy of a form and its questions with new metadata.
    """
    print(f"[DEBUG] Entering create_form_copy_view with form_id: {form_id}")

    # Attempt to retrieve the original form
    try:
        original_form = get_object_or_404(Form, id=form_id)
        print(f"[DEBUG] Original form retrieved: {original_form}")
    except Exception as e:
        print(f"[ERROR] Could not retrieve original form: {e}")
        return JsonResponse({'error': 'Original form not found.'}, status=404)

    if request.method == 'POST':
        print("[DEBUG] Processing POST request")
        
        # Get new metadata from the request
        name = request.POST.get('name')
        part_number = request.POST.get('part_number')
        operation = request.POST.get('operation')

        print(f"[DEBUG] Received POST data: name={name}, part_number={part_number}, operation={operation}")

        # Check for missing fields
        if not name or not part_number or not operation:
            print("[ERROR] Missing required fields in POST data")
            return JsonResponse({'error': 'All fields (name, part_number, operation) are required.'}, status=400)

        try:
            # Create the new form instance with new metadata
            new_form = Form.objects.create(
                name=name,
                form_type=original_form.form_type,
                metadata={
                    'part_number': part_number,
                    'operation': operation,
                    **{k: v for k, v in original_form.metadata.items() if k not in ['part_number', 'operation']}
                }
            )
            print(f"[DEBUG] New form created: {new_form}")
        except Exception as e:
            print(f"[ERROR] Failed to create new form: {e}")
            return JsonResponse({'error': 'Failed to create a new form.'}, status=500)

        try:
            # Copy all questions from the original form to the new form
            for question in original_form.questions.all():
                FormQuestion.objects.create(
                    form=new_form,
                    question=question.question
                )
            print(f"[DEBUG] Questions copied to new form (id={new_form.id})")
        except Exception as e:
            print(f"[ERROR] Failed to copy questions: {e}")
            return JsonResponse({'error': 'Failed to copy questions to the new form.'}, status=500)

        # Return a success message
        return JsonResponse({'message': f'Successfully created a copy of the form: {new_form.name}.'}, status=200)

    return JsonResponse({'error': 'Invalid request method.'}, status=405)







@csrf_exempt
def process_selected_forms(request):
    if request.method == "POST":
        print("[DEBUG] Received POST request")
        # Normalize form IDs (handle both list and comma-separated strings)
        raw_form_ids = request.POST.getlist('form_ids[]')
        form_ids = []
        for item in raw_form_ids:
            form_ids.extend(item.split(','))
        print("[DEBUG] Parsed form_ids:", form_ids)
        
        # Get form type from POST data
        form_type = request.POST.get("form_type", "").upper()
        if not form_type:
            return JsonResponse({"error": "Form type not provided."}, status=400)
        
        # Choose the appropriate question form class based on form_type.
        if form_type == "OIS":
            question_form_class = OISQuestionForm
        elif form_type == "LPA":
            question_form_class = LPAQuestionForm
        else:
            return JsonResponse({"error": "Unsupported form type."}, status=400)
        
        # Instantiate the form with POST data.
        question_form = question_form_class(request.POST)
        if not question_form.is_valid():
            # Return errors from the form's validation.
            errors = question_form.errors.as_json()
            print("[ERROR] Form errors:", errors)
            return JsonResponse({"error": "Invalid form data.", "details": errors}, status=400)
        
        # If the form is valid, loop over each selected form and add the question.
        for form_id in form_ids:
            try:
                form_instance = Form.objects.get(id=form_id)
                # Save the question and associate it with the form instance.
                question_form.save(form_instance=form_instance)
                print(f"[DEBUG] Question added for form {form_id}")
            except Form.DoesNotExist:
                return JsonResponse({"error": f"Form with ID {form_id} not found."}, status=404)
            except Exception as e:
                print(f"[ERROR] Unexpected error for form {form_id}: {e}")
                return JsonResponse({"error": f"Failed to create question for form {form_id}."}, status=500)
        
        print("[DEBUG] All questions added successfully")
        return JsonResponse({"message": "Question added successfully!", "form_ids": form_ids})

    elif request.method == "GET":
        print("[DEBUG] Received GET request for modal form")
        # Get the form type from GET data.
        form_type = request.GET.get("form_type", "").upper()
        print("[DEBUG] Form type received:", form_type)
        if form_type == "OIS":
            form = OISQuestionForm()
        elif form_type == "LPA":
            form = LPAQuestionForm()
        else:
            # Default fallback or error.
            print("[DEBUG] Unknown form_type provided, defaulting to LPAQuestionForm")
            form = LPAQuestionForm()
        
        form_html = render_to_string(
            "forms/question_form.html",
            {"form": form},
            request=request,
        )
        print("[DEBUG] Returning rendered form HTML")
        return JsonResponse({"form_html": form_html})

    else:
        print(f"[ERROR] Invalid request method: {request.method}")
        return JsonResponse({"error": "Invalid request method"}, status=400)






@csrf_exempt
def process_form_deletion(request):
    if request.method == "POST":
        form_id = request.POST.get("form_id")
        if not form_id:
            return JsonResponse({"error": "Form ID not provided."}, status=400)

        try:
            # Retrieve the form and update its metadata
            form = Form.objects.get(id=form_id)
            form.metadata["deleted"] = True  # Add "deleted": true to metadata
            form.save()  # Save changes
            print(f"[DEBUG] Form {form_id} marked as deleted.")
            return JsonResponse({"message": f"Form {form_id} marked as deleted successfully!"})
        except Form.DoesNotExist:
            print(f"[ERROR] Form with ID {form_id} not found.")
            return JsonResponse({"error": f"Form with ID {form_id} not found."}, status=404)
        except Exception as e:
            print(f"[ERROR] Unexpected error: {e}")
            return JsonResponse({"error": "An error occurred while marking the form as deleted."}, status=500)
    else:
        return JsonResponse({"error": "Invalid request method."}, status=400)