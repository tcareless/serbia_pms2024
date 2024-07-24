# plant/urls.py

from django.urls import path
from .views import (
    display_setups, create_setupfor, edit_setupfor, delete_setupfor,
    display_assets, create_asset, edit_asset, delete_asset,
    display_parts, create_part, edit_part, delete_part
)

urlpatterns = [
    path('setups/', display_setups, name='display_setups'),
    path('setups/create/', create_setupfor, name='create_setupfor'),
    path('setups/edit/<int:id>/', edit_setupfor, name='edit_setupfor'),
    path('setups/delete/<int:id>/', delete_setupfor, name='delete_setupfor'),
    path('assets/', display_assets, name='display_assets'),
    path('assets/create/', create_asset, name='create_asset'),
    path('assets/edit/<int:id>/', edit_asset, name='edit_asset'),
    path('assets/delete/<int:id>/', delete_asset, name='delete_asset'),
    path('parts/', display_parts, name='display_parts'),
    path('parts/create/', create_part, name='create_part'),
    path('parts/edit/<int:id>/', edit_part, name='edit_part'),
    path('parts/delete/<int:id>/', delete_part, name='delete_part'),
]
