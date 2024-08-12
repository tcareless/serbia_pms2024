from django.urls import path
from .views import scrap_form, index

urlpatterns = [
    path('', index, name='index'),
    path('scrap_form/', scrap_form, name='scrap_form'),

]
