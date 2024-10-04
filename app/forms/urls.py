from django.urls import path
from .views import (
    FormTypeListView, FormTypeCreateView, FormTypeUpdateView, FormTypeDeleteView,
    FormListView, FormCreateView, FormUpdateView, FormDeleteView,
    QuestionListView, QuestionCreateView, QuestionUpdateView, QuestionDeleteView,
    AnswerListView, AnswerCreateView, AnswerUpdateView, AnswerDeleteView,

)
from .views import ois_form_view


urlpatterns = [
    # FormType URLs
    path('formtypes/', FormTypeListView.as_view(), name='formtype_list'),
    path('formtypes/new/', FormTypeCreateView.as_view(), name='formtype_create'),
    path('formtypes/<int:pk>/edit/', FormTypeUpdateView.as_view(), name='formtype_edit'),
    path('formtypes/<int:pk>/delete/', FormTypeDeleteView.as_view(), name='formtype_delete'),

    # Form URLs
    path('forms/', FormListView.as_view(), name='form_list'),
    path('forms/new/', FormCreateView.as_view(), name='form_create'),
    path('forms/<int:pk>/edit/', FormUpdateView.as_view(), name='form_edit'),
    path('forms/<int:pk>/delete/', FormDeleteView.as_view(), name='form_delete'),

    # Question URLs
    path('forms/<int:form_id>/questions/', QuestionListView.as_view(), name='question_list'),
    path('forms/<int:form_id>/questions/new/', QuestionCreateView.as_view(), name='question_create'),
    path('questions/<int:pk>/edit/', QuestionUpdateView.as_view(), name='question_edit'),
    path('questions/<int:pk>/delete/', QuestionDeleteView.as_view(), name='question_delete'),

    # Answer URLs
    path('questions/<int:question_id>/answers/', AnswerListView.as_view(), name='answer_list'),
    path('questions/<int:question_id>/answers/new/', AnswerCreateView.as_view(), name='answer_create'),
    path('answers/<int:pk>/edit/', AnswerUpdateView.as_view(), name='answer_edit'),
    path('answers/<int:pk>/delete/', AnswerDeleteView.as_view(), name='answer_delete'),

    path('ois/form/<int:form_id>/', ois_form_view, name='ois_form'),

]
