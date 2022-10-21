from django.urls import path

from . import views

urlpatterns = [
    path('input', views.dup_scan, name='dup-scan'),
]
