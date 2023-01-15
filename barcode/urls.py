from django.urls import path

from . import views

urlpatterns = [
    path('duplicate', views.duplicate_scan, name='duplicate-scan'),
    # path('quality', views.quality_scan, name='quality-scan'),
]
