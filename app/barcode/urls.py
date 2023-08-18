from django.urls import path
from django.views.generic.base import RedirectView
from . import views

app_name = "barcode"

urlpatterns = [
    path('index/', views.barcode_index_view, name='barcode_index'),

    path('', RedirectView.as_view(pattern_name='duplicate-scan')),
    path('duplicate', views.duplicate_scan, name='duplicate-scan'),
    path('duplicate_check', views.duplicate_scan_check,
         name='duplicate-scan-check'),
    path('duplicate_batch',
         views.duplicate_scan_batch, name='duplicate_scan_batch'),
    path('query', views.query, name='query'),
    path('laser_count', views.laser_count, name='laser_count'),
    # path('quality', views.quality_scan, name='quality-scan'),
]
