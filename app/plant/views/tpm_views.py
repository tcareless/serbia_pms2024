from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.db.models import Prefetch
from ..models.tpm_models import TPM_Questionaire, Questions, TPM_Answers
from django.views.decorators.csrf import csrf_exempt
from ..models.setupfor_models import Asset
from django.utils import timezone
from django.db.models import Max
from django.utils.timezone import now
from django.http import Http404
from django.core.serializers.json import DjangoJSONEncoder
import json
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.urls import reverse
import time


# ========================================================================
# ========================================================================
# ======================== Questionaires =================================
# ========================================================================
# ========================================================================

def manage_page(request, asset_number=None):
    # Fetch all assets to populate the dropdown
    all_assets = Asset.objects.all()

    if not asset_number:
        # No asset selected, render the page with just the dropdown
        context = {
            'asset': None,
            'asset_number': None,
            'all_assets': all_assets,  # Pass all assets for the dropdown
            'questions_by_group': {},
            'all_questions_by_group': json.dumps({}, cls=DjangoJSONEncoder),
            'expanded_group': None,  # No expanded group initially
        }
        return render(request, 'manage.html', context)

    # Fetch the selected asset
    asset = get_object_or_404(Asset, asset_number=asset_number)

    # Fetch all distinct question groups dynamically
    question_groups = Questions.objects.values_list('question_group', flat=True).distinct()

    # Fetch related questionnaires and group questions by question_group
    questionaires = asset.questionaires.prefetch_related('questions')
    questions_by_group = {group: [] for group in question_groups}  # Initialize all groups

    for questionaire in questionaires:
        for question in questionaire.questions.filter(deleted=False):
            questions_by_group[question.question_group].append(question)

    # Ensure all_questions_by_group uses correct fields
    all_questions_by_group = {
        group: list(Questions.objects.filter(question_group=group, deleted=False).values('id', 'question'))
        for group in question_groups
    }

    # Extract the expanded group from query parameters
    expanded_group = request.GET.get('expanded_group', None)
    if not expanded_group and question_groups:  # Default to the first group if no expanded_group is provided
        expanded_group = question_groups[0]

    context = {
        'asset': asset,
        'asset_number': asset_number,
        'all_assets': all_assets,
        'questions_by_group': questions_by_group,
        'all_questions_by_group': json.dumps(all_questions_by_group, cls=DjangoJSONEncoder),
        'expanded_group': expanded_group,
    }
    return render(request, 'manage.html', context)





def add_question(request, asset_number):
    if request.method == "POST":
        question_group = request.POST.get('question_group')
        existing_question_id = request.POST.get('existing_question')
        new_question_text = request.POST.get('new_question')
        question_type = request.POST.get('question_type')

        # Fetch the Asset using asset_number
        asset = get_object_or_404(Asset, asset_number=asset_number)

        # Fetch or create the TPM_Questionaire for the asset
        questionaire, created = TPM_Questionaire.objects.get_or_create(asset=asset)

        # Handle existing question selection
        if existing_question_id:
            question = Questions.objects.get(id=existing_question_id)
        else:
            # Create a new question
            question = Questions.objects.create(
                question=new_question_text,
                question_group=question_group,
                type=question_type
            )

        # Add the question to the questionaire
        questionaire.questions.add(question)

        # Redirect back to the manage page with the question_group as a query parameter
        return HttpResponseRedirect(
            f"{reverse('plant:manage_page', args=[asset.asset_number])}?expanded_group={question_group}"
        )

    raise Http404("Invalid request")


def remove_question(request, asset_number):
    if request.method == "POST":
        question_id = request.POST.get('question_id')
        
        if not question_id:
            messages.error(request, "No question ID provided.")
            return redirect('plant:manage_page', asset_number=asset_number)

        # Fetch the asset and question
        asset = get_object_or_404(Asset, asset_number=asset_number)
        question = get_object_or_404(Questions, id=question_id)
        
        # Remove only the specific association
        questionaire = TPM_Questionaire.objects.filter(asset=asset).first()
        if questionaire and question in questionaire.questions.all():
            questionaire.questions.remove(question)
            messages.success(request, f"Question '{question.question}' removed from asset.")
        else:
            messages.error(request, f"Question not associated with this asset.")

        return redirect('plant:manage_page', asset_number=asset_number)

    raise Http404("Invalid request")



def operator_form(request, asset_number):
    asset = get_object_or_404(Asset, asset_number=asset_number)

    if request.method == "POST":
        # Extract submitted data
        operator_number = request.POST.get("operator")
        shift = request.POST.get("shift")
        date = request.POST.get("date")

        # Prepare answers
        answers = {}
        for key, value in request.POST.items():
            if key.startswith("question_"):
                question_id = key.split("_")[1]
                answers[question_id] = value

        # Save to TPM_Answers table
        TPM_Answers.objects.create(
            asset=asset,
            operator_number=operator_number,
            shift=shift,
            date=date,
            answers=answers,
            submitted_at=int(time.time())  # Set epoch timestamp
        )

        # Redirect or return a success response
        return JsonResponse({"message": "Form submitted successfully!"}, status=200)

    # For GET requests, render the form
    questionaire = TPM_Questionaire.objects.filter(asset=asset).order_by('-effective_date').first()
    questions = questionaire.questions.filter(deleted=False).values('id', 'question', 'type') if questionaire else []
    return render(request, 'operator_form.html', {
        'asset_number': asset_number,
        'questions': questions,
        'today_date': now().strftime('%Y-%m-%d'),
    })


def edit_question(request, asset_number):
    if request.method == "POST":
        question_id = request.POST.get('question_id')
        question_text = request.POST.get('question_text')
        question_type = request.POST.get('question_type')

        # Fetch the question to update
        question = get_object_or_404(Questions, id=question_id)

        # Update the question fields
        question.question = question_text
        question.type = question_type
        question.save()

        messages.success(request, "Question updated successfully!")

        # Redirect back to the manage page
        return HttpResponseRedirect(
            f"{reverse('plant:manage_page', args=[asset_number])}?expanded_group={question.question_group}"
        )

    raise Http404("Invalid request")