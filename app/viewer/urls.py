# viewer/urls.py
from django.urls import path
from .views import rabbits_view, production, bypass_status, bypasslog, sub_index

urlpatterns = [
    path('gfx/rabbits/', rabbits_view, name='rabbits_view'),
    path('gfx/production/', production, name='production'),
    path('gfx/bypass/', bypass_status, name='bypass_status'),
    path('gfx/bypasslog/', bypasslog, name='bypasslog'),
    path('sub-index/', sub_index, name='sub-index'),  # New sub-index

]
