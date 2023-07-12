from django.urls import path
from django.views.generic.base import RedirectView
from . import views

urlpatterns = [
    path('', RedirectView.as_view(pattern_name='duplicate-scan')),
    path('gfx/scan', views.gfx_scan_view, name='gfx-scan'),
    path('gfx/batch', views.gfx_batch_view, name='gfx-batch'),
    path('gfx/check', views.gfx_check_view, name='gfx-check'),
    path('duplicate', views.duplicate_scan, name='duplicate-scan'),
    path('duplicate_check', views.duplicate_scan_check,
         name='duplicate-scan-check'),
    path('duplicate_batch',
         views.duplicate_scan_batch, name='duplicate_scan_batch'),
    # path('quality', views.quality_scan, name='quality-scan'),
]
