from django.urls import path

from . import views

urlpatterns = [
    path('cell_track_9341/', views.cell_track_9341, {'target': 'desk'}, name='track9341'),
    path('cell_track_9341_TV/', views.cell_track_9341, {'target': 'tv'}, name='track9341_TV'),
    path('cell_track_9341_mobile/', views.cell_track_9341, {'target': 'mobile'}, name='track9341_mobile'),
    

    path('1467/', views.cell_track_1467, {'template': 'cell_track_1467.html'}, name='1467'),
    path('cell_track_1467/', views.cell_track_1467, {'template': 'cell_track_1467.html'}, name='track1467'),

    path('8670/', views.cell_track_8670, {'template': 'cell_track_8670.html'}, name='ab1v'),
    path('cell_track_8670/', views.cell_track_8670, {'template': 'cell_track_8670.html'}, name='track8670'),
    path('track_graph_track/get/<str:index>/', views.track_graph_track, name='track_graph'),
]
