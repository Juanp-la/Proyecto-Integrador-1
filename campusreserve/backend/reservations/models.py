from django.conf import settings
from django.db import models

from courts.models import Court


class Reservation(models.Model):
    STATUS_CHOICES = [
        ("confirmed", "Confirmed"),
        ("cancelled", "Cancelled"),
    ]

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reservations"
    )
    court = models.ForeignKey(Court, on_delete=models.CASCADE, related_name="reservations")
    reservation_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="confirmed")
    created_at = models.DateTimeField(auto_now_add=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-reservation_date", "-start_time"]

    def __str__(self):
        return f"{self.student} · {self.court} · {self.reservation_date} {self.start_time}"
