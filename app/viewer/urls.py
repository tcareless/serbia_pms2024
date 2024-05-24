# viewer/urls.py
from django.urls import path
from .views import rabbits_view

urlpatterns = [
    path('gfx/rabbits/', rabbits_view, name='rabbits_view'),
]
