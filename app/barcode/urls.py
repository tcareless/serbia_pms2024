from django.urls import path
from django.views.generic.base import RedirectView
from . import views

app_name = "barcode"

urlpatterns = [
    path('index/', views.barcode_index_view, name='barcode_index'),

    path('', RedirectView.as_view(pattern_name='duplicate-scan')),
    path('gfx/scan', views.gfx_scan_view, name='gfx-scan'),
    path('gfx/batch', views.gfx_batch_view, name='gfx-batch'),
    path('gfx/check', views.gfx_check_view, name='gfx-check'),
    path('duplicate', views.scan_view, name='duplicate-scan'),
    path('duplicate_check', views.check_view,
         name='duplicate-scan-check'),
    path('duplicate_batch',
         views.batch_view, name='duplicate_scan_batch'),
    # path('quality', views.quality_scan, name='quality-scan'),
]
