from django.shortcuts import render, get_object_or_404, redirect
from .forms import FormTypeForm
from django.utils import timezone
import json
from .models import FormSubmission, FormType
from django.utils import timezone


# ===========================================================================
# ===========================================================================
# ========================== FORM TYPE VIEWS ================================
# ===========================================================================
# ===========================================================================


def index(request):
    return render(request, 'forms/index.html')

def form_type_list(request):
    form_types = FormType.objects.all()
    return render(request, 'forms/form_types/form_type_list.html', {'form_types': form_types})

def form_type_create(request):
    if request.method == 'POST':
        form = FormTypeForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('form_type_list')
    else:
        form = FormTypeForm()
    return render(request, 'forms/form_types/form_type_form.html', {'form': form})

def form_type_update(request, pk):
    form_type = get_object_or_404(FormType, pk=pk)
    if request.method == 'POST':
        form = FormTypeForm(request.POST, instance=form_type)
        if form.is_valid():
            form.save()
            return redirect('form_type_list')
    else:
        form = FormTypeForm(instance=form_type)
    return render(request, 'forms/form_types/form_type_form.html', {'form': form})

def form_type_delete(request, pk):
    form_type = get_object_or_404(FormType, pk=pk)
    if request.method == 'POST':
        form_type.delete()
        return redirect('form_type_list')
    return render(request, 'forms/form_types/form_type_confirm_delete.html', {'form_type': form_type})

def tool_life_form(request):
    if request.method == 'POST':
        form_type = FormType.objects.get(name='Tool Life Forms')  # Use the existing FormType
        payload = {
            'tool_type': request.POST.get('tool_type'),
            'tool_condition': request.POST.get('tool_condition'),
            'tool_life_hours': request.POST.get('tool_life_hours'),
            'tool_notes': request.POST.get('tool_notes')
        }
        FormSubmission.objects.create(
            payload=payload,
            form_type=form_type,
            created_at=timezone.now()
        )
    return render(request, 'forms/tool_life_form.html')




# =======================================================================
# =======================================================================
# ========================= DUMMY TEST VIEWS ============================
# =======================================================================
# =======================================================================


from django.shortcuts import render, redirect
from .models import FormSubmission, FormType
from django.utils import timezone

def inspection_tally_sheet(request):
    if request.method == 'POST':
        form_type = FormType.objects.get(name='100% Inspection Tally Sheet')  # Use the existing FormType
        payload = {
            'inspector_name': request.POST.get('inspector_name'),
            'inspection_date': request.POST.get('inspection_date'),
            'units_inspected': request.POST.get('units_inspected'),
            'units_passed': request.POST.get('units_passed')
        }
        FormSubmission.objects.create(
            payload=payload,
            form_type=form_type,
            created_at=timezone.now()
        )
    return render(request, 'forms/inspection_tally_sheet.html')  # Use the template name associated with the FormType




# ====================================================================
# ====================================================================
# ========================== FORMS VIEWS =============================
# ====================================================================
# ====================================================================


from django.shortcuts import render, get_object_or_404, redirect
from .models import Form, FormQuestionAnswer, FormType
from .forms import FormForm, FormQuestionAnswerForm

# Form Views
def form_list(request):
    forms = Form.objects.all()
    return render(request, 'forms/forms/form_list.html', {'forms': forms})

def form_create(request):
    if request.method == 'POST':
        form = FormForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('form_list')
    else:
        form = FormForm()
    return render(request, 'forms/forms/form_form.html', {'form': form})

def form_update(request, pk):
    form_instance = get_object_or_404(Form, pk=pk)
    if request.method == 'POST':
        form = FormForm(request.POST, instance=form_instance)
        if form.is_valid():
            form.save()
            return redirect('form_list')
    else:
        form = FormForm(instance=form_instance)
    return render(request, 'forms/forms/form_form.html', {'form': form})

def form_delete(request, pk):
    form_instance = get_object_or_404(Form, pk=pk)
    if request.method == 'POST':
        form_instance.delete()
        return redirect('form_list')
    return render(request, 'forms/forms/form_confirm_delete.html', {'form': form_instance})


# =====================================================================================
# =====================================================================================
# ==================================Question & Answer Views ===========================
# =====================================================================================
# =====================================================================================



# FormQuestionAnswer Views
def form_question_answer_list(request, form_pk):
    form = get_object_or_404(Form, pk=form_pk)
    questions_answers = form.questions_answers.all()
    return render(request, 'forms/questions_answers/form_question_answer_list.html', {
        'form': form, 
        'questions_answers': questions_answers
    })

def form_question_answer_create(request, form_pk):
    form_instance = get_object_or_404(Form, pk=form_pk)
    if request.method == 'POST':
        question_answer_form = FormQuestionAnswerForm(request.POST)
        if question_answer_form.is_valid():
            question_answer = question_answer_form.save(commit=False)
            question_answer.form = form_instance
            question_answer.save()
            return redirect('form_question_answer_list', form_pk=form_pk)
    else:
        question_answer_form = FormQuestionAnswerForm()
    return render(request, 'forms/questions_answers/form_question_answer_form.html', {
        'form': form_instance, 
        'question_answer_form': question_answer_form
    })

def form_question_answer_update(request, pk):
    question_answer = get_object_or_404(FormQuestionAnswer, pk=pk)
    if request.method == 'POST':
        question_answer_form = FormQuestionAnswerForm(request.POST, instance=question_answer)
        if question_answer_form.is_valid():
            question_answer_form.save()
            return redirect('form_question_answer_list', form_pk=question_answer.form.pk)
    else:
        question_answer_form = FormQuestionAnswerForm(instance=question_answer)
    return render(request, 'forms/questions_answers/form_question_answer_form.html', {
        'form': question_answer.form, 
        'question_answer_form': question_answer_form
    })

def form_question_answer_delete(request, pk):
    question_answer = get_object_or_404(FormQuestionAnswer, pk=pk)
    if request.method == 'POST':
        form_pk = question_answer.form.pk
        question_answer.delete()
        return redirect('form_question_answer_list', form_pk=form_pk)
    return render(request, 'forms/questions_answers/form_question_answer_confirm_delete.html', {
        'question_answer': question_answer
    })






# =====================================================================================
# =====================================================================================
# =========================== Tool Life Forms =========================================
# =====================================================================================
# =====================================================================================

