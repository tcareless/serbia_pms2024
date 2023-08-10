from django.urls import path

from . import views

app_name = "prod_query"

urlpatterns = [
    path('index/', views.prod_query_index_view, name='prod-query_index'),
    path('', views.prod_query, name='prod-query'),
    path('rejects', views.reject_query, name='rejects'),
    path('cycle-times', views.cycle_times, name='cycle-times'),
    path('<str:machine>/<int:start_timestamp>/<int:times>/', views.machine_detail, name='machine_detail'),
]
