from django.urls import path

from . import views

urlpatterns = [
    path('10R80/', views.cell_track_9341, {'template': 'cell_track_9341.html'}, name='10R80'),
    path('cell_track_9341/', views.cell_track_9341, {'template': 'cell_track_9341.html'}, name='track9341'),
    path('cell_track_9341_TV/', views.cell_track_9341, {'template': 'cell_track_9341.html'}, name='track9341_TV'),
    path('cell_track_9341_mobile/', views.cell_track_9341, {'template': 'cell_track_9341_mobile.html'}, name='track9341_mobile'),

    path('1467/', views.cell_track_1467, {'template': 'cell_track_1467.html'}, name='1467'),
    path('cell_track_1467/', views.cell_track_1467, {'template': 'cell_track_1467.html'}, name='track1467'),

    path('8670/', views.cell_track_8670, {'template': 'cell_track_8670.html'}, name='ab1v'),
    path('cell_track_8670/', views.cell_track_8670, {'template': 'cell_track_8670.html'}, name='track8670'),
]
