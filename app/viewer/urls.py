# viewer/urls.py
from django.urls import path
from .views import rabbits_view, production, bypass_status, bypasslog, sub_index

urlpatterns = [
    path('gfx/rabbits/', rabbits_view, name='rabbits_view'),
    path('production/', production, name='production'),
    path('bypass/', bypass_status, name='bypass_status'),
    path('bypasslog/', bypasslog, name='bypasslog'),
    path('sub-index/', sub_index, name='sub-index'),  # New sub-index

]
