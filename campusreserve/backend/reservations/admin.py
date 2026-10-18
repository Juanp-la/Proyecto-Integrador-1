from django.contrib import admin

from .models import Reservation


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ["student", "court", "reservation_date", "start_time", "end_time", "status"]
    list_filter = ["status", "court"]
