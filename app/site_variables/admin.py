from django.contrib import admin

# Register your models here.
from .models import SiteVariableModel

class SiteVariableAdmin(admin.ModelAdmin):
    list_display = ("variable_name", "variable_value")
    list_editable = ("variable_value",)

admin.site.register(SiteVariableModel, SiteVariableAdmin)