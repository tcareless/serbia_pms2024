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
]
