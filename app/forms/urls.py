from django.urls import path
from .views import *

urlpatterns = [
    path('', index, name='forms_index'),
    # FormType URLs
    path('formtypes/', FormTypeListView.as_view(), name='formtype_list'),
    path('formtypes/new/', FormTypeCreateView.as_view(), name='formtype_create'),
    path('formtypes/<int:pk>/edit/', FormTypeUpdateView.as_view(), name='formtype_edit'),
    path('formtypes/<int:pk>/delete/', FormTypeDeleteView.as_view(), name='formtype_delete'),

    path('create/', form_create_view, name='form_create'),
    path('edit/<int:form_id>/', form_create_view, name='form_edit'),  # Edit form URL
    path('find/', find_forms_view, name='find_forms'),  # Add this new URL


    path('bulk_question_create/', bulk_form_and_question_create_view, name='bulk_question_create'),


    path('form/<int:form_id>/', form_questions_view, name='form_questions'),
    path('form/', form_by_metadata_view, name='form_by_metadata'),

    path('smart_form/<int:form_id>/', smart_form_redirect_view, name='smart_form'),


    path('form/<int:form_id>/records/', view_records, name='view_records'),  # New URL for viewing records


    path('lpa_closeout/', lpa_closeout_view, name='lpa_closeout'),

    path('closed_lpas/', closed_lpas_view, name='closed_lpas'),

    path('form/<int:form_id>/create-copy/', create_form_copy_view, name='create_form_copy'),

    path('process-selected-forms/', process_selected_forms, name='process_selected_forms'),

]
