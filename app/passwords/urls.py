# passwords/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.password_list, name='password_list'),
    path('new/', views.password_create, name='password_create'),
    path('edit/<int:pk>/', views.password_edit, name='password_edit'),
    path('delete/<int:pk>/', views.password_delete, name='password_delete'),
    path('recover/<int:pk>/', views.password_recover, name='password_recover'),
    path('deleted/', views.deleted_passwords, name='deleted_passwords'),
    path('auth/', views.auth_page, name='auth_page'),

]
