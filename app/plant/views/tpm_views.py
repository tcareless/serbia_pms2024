from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.db.models import Prefetch
from ..models.tpm_models import TPM_Questionaire, Questions, TPM_Answers, QuestionaireQuestion
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
    all_assets = Asset.objects.all()

    if not asset_number:
        context = {
            'asset': None,
            'asset_number': None,
            'all_assets': all_assets,
            'questions_by_group': {},
            'all_questions_by_group': json.dumps({}, cls=DjangoJSONEncoder),
            'expanded_group': None,
        }
        return render(request, 'manage.html', context)

    asset = get_object_or_404(Asset, asset_number=asset_number)

    question_groups = Questions.objects.values_list('question_group', flat=True).distinct()

    questionaires = asset.questionaires.prefetch_related('questionaire_questions__question')
    questions_by_group = {group: [] for group in question_groups}

    for questionaire in questionaires:
        for link in questionaire.questionaire_questions.order_by('order'):
            question = link.question
            if not question.deleted:
                questions_by_group[question.question_group].append({
                    'id': question.id,
                    'question': question.question,
                    'type': question.type,
                    'order': link.order,  # Include order from the QuestionaireQuestion model
                })
                
    all_questions_by_group = {
        group: list(Questions.objects.filter(question_group=group, deleted=False).values('id', 'question'))
        for group in question_groups
    }

    expanded_group = request.GET.get('expanded_group', None)
    if not expanded_group and question_groups:
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
        order = request.POST.get('order', 0.0)  # Default to 0.0 if not provided

        asset = get_object_or_404(Asset, asset_number=asset_number)
        questionaire, created = TPM_Questionaire.objects.get_or_create(asset=asset)

        if existing_question_id:
            question = Questions.objects.get(id=existing_question_id)
        else:
            question = Questions.objects.create(
                question=new_question_text,
                question_group=question_group,
                type=question_type
            )

        # Add question using the intermediate model with the specified order
        QuestionaireQuestion.objects.create(
            questionaire=questionaire,
            question=question,
            order=float(order)
        )

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

        asset = get_object_or_404(Asset, asset_number=asset_number)
        question = get_object_or_404(Questions, id=question_id)

        questionaire = TPM_Questionaire.objects.filter(asset=asset).first()
        if questionaire:
            link = QuestionaireQuestion.objects.filter(
                questionaire=questionaire,
                question=question
            ).first()
            if link:
                link.delete()
                messages.success(request, f"Question '{question.question}' removed from asset.")
            else:
                messages.error(request, "Question not associated with this asset.")
        else:
            messages.error(request, "No questionnaire found for the asset.")

        return redirect('plant:manage_page', asset_number=asset_number)

    raise Http404("Invalid request")



def operator_form(request, asset_number):
    asset = get_object_or_404(Asset, asset_number=asset_number)

    if request.method == "POST":
        operator_number = request.POST.get("operator")
        shift = request.POST.get("shift")
        date = request.POST.get("date")

        answers = {}
        for key, value in request.POST.items():
            if key.startswith("question_"):
                question_id = key.split("_")[1]
                answers[question_id] = value

        TPM_Answers.objects.create(
            asset=asset,
            operator_number=operator_number,
            shift=shift,
            date=date,
            answers=answers,
            submitted_at=int(time.time())
        )

        return JsonResponse({"message": "Form submitted successfully!"}, status=200)

    questionaire = TPM_Questionaire.objects.filter(asset=asset).order_by('-effective_date').first()
    questions = QuestionaireQuestion.objects.filter(
        questionaire=questionaire,
        question__deleted=False
    ).values('question__id', 'question__question', 'question__type') if questionaire else []

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