from django.contrib import admin

from .models import LaserMark, BarCodePUN


@admin.register(LaserMark)
class LaserMarkAdmin(admin.ModelAdmin):

    list_display = ('bar_code', 'part_number')
    list_filter = ('created_at',)

    search_fields = ('bar_code', 'part_number')


@admin.register(BarCodePUN)
class BarCodePUNAdmin(admin.ModelAdmin):

    list_display = ('name', 'part_number', 'regex', 'active', 'parts_per_tray')
    list_filter = ('active', 'part_number')

    search_fields = ('name', 'part_number')
