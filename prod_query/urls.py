from django.urls import path

from . import views

urlpatterns = [
    path('shift-line', views.shift_line, name='shift-line'),
    path('rar', views.uplift_rar, name='rar'),
    path('test', views.test, name='test'),

]
