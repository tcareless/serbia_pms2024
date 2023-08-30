from django.urls import path

from . import views

app_name = "part_for_machine"

urlpatterns = [
    path('', views.part_for_machine, name='part_for_machine')
]
