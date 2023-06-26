from django.urls import path
from django.views.generic.base import RedirectView
from . import views

urlpatterns = [
    path('', RedirectView.as_view(pattern_name='duplicate-scan')),
    path('duplicate', views.duplicate_scan, name='duplicate-scan'),
    path('duplicate_check', views.duplicate_scan_check,
         name='duplicate-scan-check'),
    path('duplicate_batch',
         views.duplicate_scan_batch, name='duplicate_scan_batch'),
    path('query', views.query, name='query'),
    # path('quality', views.quality_scan, name='quality-scan'),
]
