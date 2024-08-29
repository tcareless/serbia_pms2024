from django.urls import path
from . import views

urlpatterns = [
    path('send-emails/', views.send_emails_view, name='send_emails'),
    path('counter/', views.counter_view, name='counter'),
]
