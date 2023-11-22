from django.urls import path

from . import views
from .views import prod_query_index_view, prod_query, weekly_prod, reject_query, cycle_times, machine_detail

app_name = "prod_query"

urlpatterns = [
    path('index/', prod_query_index_view, name='prod-query_index'),
    path('', prod_query, name='prod-query'),
    # path('test', views.weekly_summary, name='weekly-summary'),
    path('weekly-prod/<int:year>/<int:week_number>', weekly_prod, name='weekly-prod'),
    path('weekly-prod', weekly_prod, name='weekly-prod'),
    path('rejects', reject_query, name='rejects'),
    path('cycle-times', cycle_times, name='cycle-times'),
    path('<str:machine>/<int:start_timestamp>/<int:times>/',
         machine_detail, name='machine_detail'),
    
]
