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
# ======================== Questions =====================================
# ========================================================================
# ========================================================================

# List all questions
def list_questions(request):
    print("Debug: Entered list_questions view")
    questions = Questions.objects.all()
    print(f"Debug: Retrieved {questions.count()} questions")
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':  # Handle AJAX request
        questions_data = [
            {'id': q.id, 'question': q.question, 'question_group': q.question_group}
            for q in questions
        ]
        print("Debug: Returning AJAX response with questions data")
        return JsonResponse({'questions': questions_data})
    print("Debug: Rendering questions.html with context")
    return render(request, 'questions.html', {'questions': questions})


@csrf_exempt
def create_question(request):
    if request.method == 'POST':
        question_text = request.POST.get('question')
        question_group = request.POST.get('question_group')
        
        # Validate that the question_group is in the allowed choices
        valid_groups = [choice[0] for choice in Questions._meta.get_field('question_group').choices]
        if question_group not in valid_groups:
            return JsonResponse({'error': 'Invalid question group'}, status=400)

        # Create the question in the database
        question = Questions.objects.create(question=question_text, question_group=question_group)
        
        # Return the created question as JSON
        return JsonResponse({
            'id': question.id,
            'question': question.question,
            'question_group': question.question_group
        })
    return JsonResponse({'error': 'Invalid request'}, status=400)


@csrf_exempt
def delete_question(request):
    if request.method == 'POST':
        question_id = request.POST.get('id')
        try:
            question = Questions.objects.get(id=question_id)
            question.delete()
            return JsonResponse({'message': 'Question deleted successfully'})
        except Questions.DoesNotExist:
            return JsonResponse({'error': 'Question not found'}, status=404)
    return JsonResponse({'error': 'Invalid request'}, status=400)


@csrf_exempt
def edit_question(request):
    if request.method == 'POST':
        question_id = request.POST.get('id')
        question_text = request.POST.get('question')
        question_group = request.POST.get('question_group')

        try:
            question = Questions.objects.get(id=question_id)
            question.question = question_text
            question.question_group = question_group
            question.save()

            return JsonResponse({
                'id': question.id,
                'question': question.question,
                'question_group': question.question_group
            })
        except Questions.DoesNotExist:
            return JsonResponse({'error': 'Question not found'}, status=404)
    return JsonResponse({'error': 'Invalid request'}, status=400)



# ========================================================================
# ========================================================================
# ======================== Questionaires =================================
# ========================================================================
# ========================================================================

# Manage Page View
def manage_page(request):
    # Fetch all assets
    assets = Asset.objects.all()
    return render(request, 'manage.html', {'assets': assets})


# API to fetch questions for a specific asset
def fetch_questions_for_asset(request):
    asset_id = request.GET.get('asset_id')
    if not asset_id:
        return JsonResponse({'error': 'Asset ID is required'}, status=400)

    # Fetch the latest questionaire for the asset based on effective_date
    try:
        latest_questionaire = TPM_Questionaire.objects.filter(asset_id=asset_id).order_by('-effective_date').first()
        associated_question_ids = latest_questionaire.questions.values_list('id', flat=True) if latest_questionaire else []
    except TPM_Questionaire.DoesNotExist:
        associated_question_ids = []

    # Fetch all questions
    all_questions = Questions.objects.all()
    questions_data = [
        {
            'id': question.id,
            'question': question.question,
            'question_group': question.question_group,
            'associated': question.id in associated_question_ids,
        }
        for question in all_questions
    ]

    return JsonResponse({'questions': questions_data})


@csrf_exempt
def save_questionaire(request):
    if request.method == 'POST':
        asset_id = request.POST.get('asset_id')
        question_ids = request.POST.getlist('question_ids[]')  # Fetch question IDs as a list

        if not asset_id:
            return JsonResponse({'error': 'Asset ID is required'}, status=400)

        if not question_ids:
            return JsonResponse({'error': 'At least one question must be selected'}, status=400)

        # Fetch the latest questionaire for the asset and determine the new version
        latest_questionaire = TPM_Questionaire.objects.filter(asset_id=asset_id).order_by('-effective_date').first()
        new_version = latest_questionaire.version + 1 if latest_questionaire else 1

        # Create the new questionaire
        questionaire = TPM_Questionaire.objects.create(
            asset_id=asset_id,
            version=new_version,
            effective_date=now()
        )

        # Associate the selected questions with the new questionaire
        selected_questions = Questions.objects.filter(id__in=question_ids)
        questionaire.questions.set(selected_questions)

        return JsonResponse({'message': 'Questionaire saved successfully', 'questionaire_id': questionaire.id})

    return JsonResponse({'error': 'Invalid request method'}, status=405)