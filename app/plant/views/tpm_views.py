from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.db.models import Prefetch
from ..models.tpm_models import TPM_Questionaire, Questions
from django.views.decorators.csrf import csrf_exempt
from ..models.setupfor_models import Asset
from django.utils import timezone
from django.db.models import Max
from django.utils.timezone import now
from django.http import Http404
from django.core.serializers.json import DjangoJSONEncoder
import json
from django.contrib import messages



# ========================================================================
# ========================================================================
# ======================== Questionaires =================================
# ========================================================================
# ========================================================================

def manage_page(request, asset_number):
    # Fetch the asset by asset_number
    asset = get_object_or_404(Asset, asset_number=asset_number)

    # Fetch all distinct question groups dynamically
    question_groups = Questions.objects.values_list('question_group', flat=True).distinct()

    # Fetch related questionaires and group questions by question_group
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

    context = {
        'asset': asset,
        'questions_by_group': questions_by_group,
        'all_questions_by_group': json.dumps(all_questions_by_group, cls=DjangoJSONEncoder),
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

        # Redirect back to the manage page
        return redirect('plant:manage_page', asset_number=asset.asset_number)

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


