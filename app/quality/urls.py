from django.urls import path
from .views import scrap_form

urlpatterns = [
    path('', scrap_form, name='scrap_form'),
]
