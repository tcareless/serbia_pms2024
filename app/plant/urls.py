# plant/urls.py

from django.urls import path
from .views import display_setups, create_setupfor, edit_setupfor, delete_setupfor, create_asset, create_part

urlpatterns = [
    path('setups/', display_setups, name='display_setups'),
    path('setups/create/', create_setupfor, name='create_setupfor'),
    path('setups/edit/<int:id>/', edit_setupfor, name='edit_setupfor'),
    path('setups/delete/<int:id>/', delete_setupfor, name='delete_setupfor'),
    path('assets/create/', create_asset, name='create_asset'),
    path('parts/create/', create_part, name='create_part'),
]
