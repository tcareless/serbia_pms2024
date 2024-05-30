from django.urls import path
from . import views

app_name = 'tooling'

urlpatterns = [
    path('report/', views.tool_report_form, name='tool_report_form'),
    path('label/', views.label_page, name='label_page'),
    path('edit/<int:entry_id>/', views.edit_tool_entry, name='edit_tool_entry'),

]
