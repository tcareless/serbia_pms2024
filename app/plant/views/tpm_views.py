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

from django.utils.text import slugify  # Optional, for slugifying group names

def manage_page(request):
    # Fetch all assets
    assets = Asset.objects.all()

    # Fetch the latest questions grouped by question_group (excluding deleted)
    questions_grouped = {}
    for choice in Questions._meta.get_field('question_group').choices:
        group_name = choice[0]
        questions = Questions.objects.filter(question_group=group_name, deleted=False)
        if questions.exists():
            questions_grouped[group_name] = questions

    # Pass question group choices to the template
    question_group_choices = Questions._meta.get_field('question_group').choices

    return render(
        request,
        'manage.html',
        {
            'assets': assets,
            'questions_grouped': questions_grouped,
            'question_group_choices': question_group_choices,
        }
    )





@csrf_exempt
def create_question(request):
    if request.method == 'POST':
        question_text = request.POST.get('question')
        question_group = request.POST.get('question_group')
        question_type = request.POST.get('question_type')  # Get question type

        valid_groups = [choice[0] for choice in Questions._meta.get_field('question_group').choices]
        if question_group not in valid_groups:
            return JsonResponse({'error': 'Invalid question group'}, status=400)

        valid_types = [choice[0] for choice in Questions._meta.get_field('type').choices]
        if question_type not in valid_types:
            return JsonResponse({'error': 'Invalid question type'}, status=400)

        question = Questions.objects.create(
            question=question_text,
            question_group=question_group,
            type=question_type
        )

        return JsonResponse({
            'id': question.id,
            'question': question.question,
            'question_group': question.question_group,
            'type': question.type
        })
    return JsonResponse({'error': 'Invalid request'}, status=400)




@csrf_exempt
def delete_question(request):
    if request.method == 'POST':
        print("Request received to delete_question view")  # Debug print
        question_id = request.POST.get('id')
        print(f"Question ID received: {question_id}")  # Debug print
        try:
            question = Questions.objects.get(id=question_id)
            question.deleted = True
            question.save()
            print(f"Question {question_id} marked as deleted")  # Debug print
            return JsonResponse({'message': 'Question flagged as deleted successfully'})
        except Questions.DoesNotExist:
            print(f"Question {question_id} not found")  # Debug print
            return JsonResponse({'error': 'Question not found'}, status=404)
    print("Invalid request method")  # Debug print
    return JsonResponse({'error': 'Invalid request'}, status=400)

@csrf_exempt
def get_asset_questions(request):
    asset_id = request.GET.get('asset_id')
    if asset_id:
        try:
            asset = Asset.objects.get(id=asset_id)

            # Get the latest version for the asset
            latest_questionaire = TPM_Questionaire.objects.filter(asset=asset).order_by('-version').first()
            if latest_questionaire:
                question_ids = latest_questionaire.questions.values_list('id', flat=True)
                return JsonResponse({'questions': list(question_ids), 'version': latest_questionaire.version})
            return JsonResponse({'questions': [], 'version': None})
        except Asset.DoesNotExist:
            return JsonResponse({'error': 'Asset not found'}, status=404)
    return JsonResponse({'error': 'Asset ID is required'}, status=400)



@csrf_exempt
def save_asset_questions(request):
    if request.method == 'POST':
        asset_id = request.POST.get('asset_id')
        questions = request.POST.getlist('questions[]')

        try:
            asset = Asset.objects.get(id=asset_id)

            # Get the latest version for this asset
            latest_questionaire = TPM_Questionaire.objects.filter(asset=asset).order_by('-version').first()
            new_version = latest_questionaire.version + 1 if latest_questionaire else 1

            # Create a new questionnaire with incremented version
            new_questionaire = TPM_Questionaire.objects.create(
                asset=asset,
                version=new_version,
                effective_date=timezone.now()
            )

            # Associate the selected questions with the new questionnaire
            new_questionaire.questions.set(Questions.objects.filter(id__in=questions))
            new_questionaire.save()

            return JsonResponse({'message': 'Questions saved successfully', 'version': new_version})
        except Asset.DoesNotExist:
            return JsonResponse({'error': 'Asset not found'}, status=404)
    return JsonResponse({'error': 'Invalid request'}, status=400)

