from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('form-types/', views.form_type_list, name='form_type_list'),
    path('form-types/create/', views.form_type_create, name='form_type_create'),
    path('form-types/<int:pk>/update/', views.form_type_update, name='form_type_update'),
    path('form-types/<int:pk>/delete/', views.form_type_delete, name='form_type_delete'),
]
