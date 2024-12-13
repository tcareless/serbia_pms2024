from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.db.models import Prefetch
from ..models.tpm_models import TPM_Questionaire, Questions
from django.views.decorators.csrf import csrf_exempt
from ..models.setupfor_models import Asset
from django.utils import timezone
from django.db.models import Max
from django.utils.timezone import now


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

    context = {
        'asset': asset,
        'questions_by_group': questions_by_group,
    }
    return render(request, 'manage.html', context)
