from django.contrib import admin

from .models import LaserMark, BarCodePUN

@admin.register(LaserMark)
class LaserMarkAdmin(admin.ModelAdmin):

  list_display = ('bar_code', 'part_number', 'scanned_at')
  list_filter = ('scanned_at',)

  search_fields = ('bar_code','part_number')


@admin.register(BarCodePUN)
class BarCodePUNAdmin(admin.ModelAdmin):

  list_display = ('name', 'part_number', 'regex')

