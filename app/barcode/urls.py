from django.urls import path
from django.views.generic.base import RedirectView
from . import views

app_name = "barcode"

urlpatterns = [
    path('index/', views.barcode_index_view, name='barcode_index'),
    path('', RedirectView.as_view(pattern_name='barcode:duplicate-scan')),
    path('duplicate', views.duplicate_scan, name='duplicate-scan'),
    path('duplicate_check', views.duplicate_scan_check, name='duplicate-scan-check'),
    path('duplicate_batch', views.duplicate_scan_batch, name='duplicate_scan_batch'),
    path('duplicate_found', views.duplicate_found_view, name='duplicate-found'),
    path('send_new_unlock_code', views.send_new_unlock_code, name='send-new-unlock-code'),
    path('verify_unlock_code', views.duplicate_found_view, name='verify-unlock-code'),
    path('sub-index/', views.sub_index, name='sub-index'),

    path('dup_batch_lockout/', views.dup_batch_lockout_view, name='dup-batch-lockout'),  # New route
]
