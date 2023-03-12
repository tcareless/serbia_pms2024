from django.urls import path

from . import views

urlpatterns = [
    path('', views.prod_query, name='prod-query'),
    path('rejects', views.reject_query, name='rejects'),
]
