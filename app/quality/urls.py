# quality/urls.py
from django.urls import path
from .views import scrap_form_management, feat_create, feat_update, feat_delete, index, scrap_form, feat_move_up, feat_move_down

urlpatterns = [
    path('', index, name='quality_index'),
    path('scrap_form/', scrap_form, name='scrap_form'),
    path('scrap_form_management/', scrap_form_management, name='scrap_form_management'),
    path('feats/new/', feat_create, name='feat_create'),
    path('feats/<int:pk>/edit/', feat_update, name='feat_update'),
    path('feats/<int:pk>/delete/', feat_delete, name='feat_delete'),
    path('feat/move_up/<int:pk>/', feat_move_up, name='feat_move_up'),
    path('feat/move_down/<int:pk>/', feat_move_down, name='feat_move_down'),
]
