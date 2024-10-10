from django.urls import path
from .views import (
    FormTypeListView, FormTypeCreateView, FormTypeUpdateView, FormTypeDeleteView,
    FormListView, FormUpdateView, FormDeleteView, 
    DynamicFormCreateView, load_form_fields,  # Import the new combined view
    AnswerListView, AnswerCreateView, AnswerUpdateView, AnswerDeleteView,
    QuestionListView  # Make sure to import the QuestionListView
)

urlpatterns = [
    # FormType URLs
    path('formtypes/', FormTypeListView.as_view(), name='formtype_list'),
    path('formtypes/new/', FormTypeCreateView.as_view(), name='formtype_create'),
    path('formtypes/<int:pk>/edit/', FormTypeUpdateView.as_view(), name='formtype_edit'),
    path('formtypes/<int:pk>/delete/', FormTypeDeleteView.as_view(), name='formtype_delete'),

    # Form and Question Creation combined URL
    path('forms/new/', DynamicFormCreateView.as_view(), name='form_create'),
    path('forms/load-fields/', load_form_fields, name='load_form_fields'),  # AJAX endpoint
    path('forms/<int:pk>/edit/', FormUpdateView.as_view(), name='form_edit'),
    path('forms/<int:pk>/delete/', FormDeleteView.as_view(), name='form_delete'),
    
    # Form List URL
    path('forms/', FormListView.as_view(), name='form_list'),

    # Question URLs
    path('forms/<int:form_id>/questions/', QuestionListView.as_view(), name='question_list'),

    # Answer URLs (remain unchanged)
    path('questions/<int:question_id>/answers/', AnswerListView.as_view(), name='answer_list'),
    path('questions/<int:question_id>/answers/new/', AnswerCreateView.as_view(), name='answer_create'),
    path('answers/<int:pk>/edit/', AnswerUpdateView.as_view(), name='answer_edit'),
    path('answers/<int:pk>/delete/', AnswerDeleteView.as_view(), name='answer_delete'),
]
