from django.urls import path
from .views import send_email_from_topic

urlpatterns = [
    path('send/<str:email_topic>/', send_email_from_topic, name='send_email_from_topic'),
]
