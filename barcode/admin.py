from django.contrib import admin

from .models import LaserMark, BarCodePUN

@admin.register(LaserMark)
class LaserMarkAdmin(admin.ModelAdmin):

  list_display = ('bar_code', 'part_number', 'duplicate_scan_at')
  list_filter = ('created_at',)

  search_fields = ('bar_code','part_number')


@admin.register(BarCodePUN)
class BarCodePUNAdmin(admin.ModelAdmin):

  list_display = ('name', 'part_number', 'regex', 'active')
  list_filter = ('active',)

  search_fields = ('name','part_number')

