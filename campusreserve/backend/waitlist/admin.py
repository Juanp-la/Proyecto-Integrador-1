from django.contrib import admin

from .models import WaitingListEntry


@admin.register(WaitingListEntry)
class WaitingListEntryAdmin(admin.ModelAdmin):
    list_display = [
        "student", "court", "reservation_date", "queue_position", "status", "expires_at",
    ]
    list_filter = ["status", "court"]
