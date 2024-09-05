from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('form-types/', views.form_type_list, name='form_type_list'),
    path('form-types/create/', views.form_type_create, name='form_type_create'),
    path('form-types/<int:pk>/update/', views.form_type_update, name='form_type_update'),
    path('form-types/<int:pk>/delete/', views.form_type_delete, name='form_type_delete'),

    path('tool-life-form/', views.tool_life_form, name='tool_life_form'),
    path('tool-life-form/submit/', views.tool_life_form, name='tool_life_form_submit'),

    path('inspection-tally-sheet/', views.inspection_tally_sheet, name='inspection_tally_sheet'),
    path('inspection-tally-sheet/submit/', views.inspection_tally_sheet, name='inspection_tally_sheet_submit'),

    path('forms/', views.form_list, name='form_list'),
    path('forms/create/', views.form_create, name='form_create'),
    path('forms/<int:pk>/update/', views.form_update, name='form_update'),
    path('forms/<int:pk>/delete/', views.form_delete, name='form_delete'),

    path('forms/<int:form_pk>/questions/', views.form_question_answer_list, name='form_question_answer_list'),
    path('forms/<int:form_pk>/questions/create/', views.form_question_answer_create, name='form_question_answer_create'),
    path('questions/<int:pk>/update/', views.form_question_answer_update, name='form_question_answer_update'),
    path('questions/<int:pk>/delete/', views.form_question_answer_delete, name='form_question_answer_delete'),

    # URL for rendering custom form and handling form submission
    path('form/<int:form_id>/', views.render_custom_form, name='render_custom_form'),
]
