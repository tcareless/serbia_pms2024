from django.contrib import admin
from .models.setupfor_models import Asset, Part, SetupFor


@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = ('asset_number', 'asset_name')
    search_fields = ('asset_number', 'asset_name')


@admin.register(Part)
class PartAdmin(admin.ModelAdmin):
    list_display = ('part_number', 'part_name')
    search_fields = ('part_number', 'part_name')


@admin.register(SetupFor)
class SetupForAdmin(admin.ModelAdmin):
    list_display = ('asset', 'part', 'created_at', 'since')
    search_fields = ('asset__asset_number', 'part__part_number')
    list_filter = ('created_at', 'since')
    ordering = ('-created_at',)
