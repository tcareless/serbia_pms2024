# quality/urls.py

from django.urls import path
from .views import add_feat, delete_feat, update_feat, update_feat_order, scrap_form_management, feat_create, feat_update, feat_delete, index, scrap_form, feat_move_up, feat_move_down, submit_scrap_form, store_supervisor_auth, forms_page, new_manager

urlpatterns = [
    path('', index, name='quality_index'),
    path('scrap_form/', forms_page),  # Redirect /scrap_form/ without part number to /forms/
    path('scrap_form/<str:part_number>/', scrap_form, name='scrap_form'),
    path('scrap_form_management/', scrap_form_management, name='scrap_form_management'),
    path('feats/new/', feat_create, name='feat_create'),
    path('feats/<int:pk>/edit/', feat_update, name='feat_update'),
    path('feats/<int:pk>/delete/', feat_delete, name='feat_delete'),
    path('feat/move_up/<int:pk>/', feat_move_up, name='feat_move_up'),
    path('feat/move_down/<int:pk>/', feat_move_down, name='feat_move_down'),
    path('submit_scrap_form/', submit_scrap_form, name='submit_scrap_form'),  # New URL for form submission
    path('store_supervisor_auth/', store_supervisor_auth, name='store_supervisor_auth'),
    path('forms/', forms_page, name='forms_page'), 
    path('new_manager/', new_manager, name='new_manager'),  # Allow access without a part_number
    path('new_manager/<str:part_number>/', new_manager, name='new_manager'),
    path('update_feat_order/', update_feat_order, name='update_feat_order'),
    path('update_feat/', update_feat, name='update_feat'),
    path('delete_feat/', delete_feat, name='delete_feat'), 
    path('add_feat/', add_feat, name='add_feat'), 


]
