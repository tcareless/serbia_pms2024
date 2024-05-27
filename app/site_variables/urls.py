from django.urls import path

from . import views

urlpatterns = [
    path('', views.create_view, name='index'),

    path('sub-index/', views.sub_index, name='sub-index'),  # New sub-index

]