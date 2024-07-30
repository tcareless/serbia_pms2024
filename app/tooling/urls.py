from django.urls import path
from . import views


app_name = 'tooling'

urlpatterns = [
    # FormDefinition URLs
    path('forms/', views.FormListView.as_view(), name='form_list'),
    path('forms/add/', views.FormCreateView.as_view(), name='form_add'),
    path('forms/<int:pk>/', views.FormDetailView.as_view(), name='form_detail'),
    path('forms/<int:pk>/edit/', views.FormUpdateView.as_view(), name='form_edit'),
    path('forms/<int:pk>/delete/', views.FormDeleteView.as_view(), name='form_delete'),

    # FormField URLs
    path('fields/add/<int:form_id>/', views.FieldCreateView.as_view(), name='field_add'),
    path('fields/<int:pk>/edit/', views.FieldUpdateView.as_view(), name='field_edit'),
    path('fields/<int:pk>/delete/', views.FieldDeleteView.as_view(), name='field_delete'),

    # FieldOption URLs
    path('options/add/<int:field_id>/', views.OptionCreateView.as_view(), name='option_add'),
    path('options/<int:pk>/edit/', views.OptionUpdateView.as_view(), name='option_edit'),
    path('options/<int:pk>/delete/', views.OptionDeleteView.as_view(), name='option_delete'),

    # Dynamic Form URLs
    path('form/<int:form_id>/', views.DynamicFormView.as_view(), name='dynamic_form'),

]
