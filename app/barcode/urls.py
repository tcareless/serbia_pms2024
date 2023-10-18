from django.urls import path
from django.views.generic.base import RedirectView
from . import views

app_name = "barcode"

urlpatterns = [
    path('index/', views.barcode_index_view, name='barcode_index'),

    path('', RedirectView.as_view(pattern_name='barcode:duplicate-scan')),
    path('duplicate', views.duplicate_scan, name='duplicate-scan'),
    path('duplicate_check', views.duplicate_scan_check,
         name='duplicate-scan-check'),
    path('duplicate_batch',
         views.duplicate_scan_batch, name='duplicate_scan_batch'),
     path('api/verify/<str:barcode>/<str:part>', views.verify_barcode_part, name='verify_by_part'),
     path('api/grade/<str:barcode>/<str:grade>', views.verify_barcode_grade, name='verify_by_grade'),
    # path('quality', views.quality_scan, name='quality-scan'),
]
