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

    path('lockout/', views.lockout_view, name='lockout_page'),

    path('scan/', views.barcode_scan_view, name='barcode-scan'),  # Scan view
    path('scan-pick/', views.barcode_pick_view, name='barcode-scan-pick'),  # Scan pick view
    path('result/<str:barcode>/', views.barcode_result_view, name='barcode-result'),  # Results view


    path('grades-dashboard/<str:part_number>/', views.grades_dashboard, name='grades_dashboard'),

]
