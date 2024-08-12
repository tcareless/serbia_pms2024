# quality/urls.py
from django.urls import path
from .views import scrap_form_management, feat_create, feat_update, feat_delete, index, scrap_form

urlpatterns = [
    path('', index, name='index'),
    path('scrap_form/', scrap_form, name='scrap_form'),
    path('scrap_form_management/', scrap_form_management, name='scrap_form_management'),
    path('feats/new/', feat_create, name='feat_create'),
    path('feats/<int:pk>/edit/', feat_update, name='feat_update'),
    path('feats/<int:pk>/delete/', feat_delete, name='feat_delete'),
]
