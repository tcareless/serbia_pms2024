# plant/urls.py

from django.urls import path
from .views.setupfor_views import (
    index, display_setups, create_setupfor, edit_setupfor, delete_setupfor,
    display_assets, create_asset, edit_asset, delete_asset,
    display_parts, create_part, edit_part, delete_part, fetch_part_for_asset,
)
from .views.password_views import (auth_page, password_list, password_create, password_edit, password_delete, password_recover, deleted_passwords)

urlpatterns = [
    path('', index, name='index'),  # New index page URL
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
    path('api/fetch_part_for_asset/', fetch_part_for_asset, name='fetch_part_for_asset'),

]


# passwords/urls.py
urlpatterns = [
    path('password_list', password_list, name='password_list'),
    path('new/', password_create, name='password_create'),
    path('edit/<int:pk>/', password_edit, name='password_edit'),
    path('delete/<int:pk>/', password_delete, name='password_delete'),
    path('recover/<int:pk>/', password_recover, name='password_recover'),
    path('deleted/', deleted_passwords, name='deleted_passwords'),
    path('auth/', auth_page, name='auth_page'),

]
