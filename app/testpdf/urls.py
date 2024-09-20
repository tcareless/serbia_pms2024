from django.urls import path
from . import views

urlpatterns = [
    path('upload/', views.upload_pdf, name='upload_pdf'),
    path('success/', views.upload_success, name='pdf_success'),  # We will create this view next
]
