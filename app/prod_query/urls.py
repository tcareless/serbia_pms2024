from django.urls import path

from . import views

urlpatterns = [
    path('', views.prod_query, name='prod-query'),
    path('rejects', views.reject_query, name='rejects'),
    path('cycle-times', views.cycle_times, name='cycle-times'),
    path('downtime-counts', views.downtime_keyword_view, name='downtime-counts'),
    path('<str:machine>/<int:start_timestamp>/<int:times>/', views.machine_detail, name='machine_detail'),
]
