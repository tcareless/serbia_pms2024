from django.urls import path

from . import views

urlpatterns = [
    path('', views.cell_track_9341, name='track9341'),
]
