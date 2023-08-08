from django.urls import path

from . import views

app_name = "query_tracking"

urlpatterns = [
    path('', views.recentqueries_view, name='query-tracking'),
]
