# viewer/urls.py
from django.urls import path
from .views import rabbits_view, production

urlpatterns = [
    path('gfx/rabbits/', rabbits_view, name='rabbits_view'),
    path('production/', production, name='production'),

]
