from django.urls import path

from . import views

urlpatterns = [
    path('', views.recentqueries_view, name='query-tracking'),
]
