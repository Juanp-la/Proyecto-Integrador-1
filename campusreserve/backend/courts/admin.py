from django.contrib import admin

from .models import Court


@admin.register(Court)
class CourtAdmin(admin.ModelAdmin):
    list_display = ["name", "sport", "location", "is_active"]
    list_filter = ["sport", "is_active"]
