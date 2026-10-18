from django.conf import settings
from django.db import models

from courts.models import Court


class WaitingListEntry(models.Model):
    STATUS_CHOICES = [
        ("waiting", "Waiting"),
        ("notified", "Notified"),
        ("expired", "Expired"),
        ("confirmed", "Confirmed"),
        ("cancelled", "Cancelled"),
    ]

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="waitlist_entries"
    )
    court = models.ForeignKey(Court, on_delete=models.CASCADE, related_name="waitlist_entries")
    reservation_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    queue_position = models.PositiveIntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="waiting")
    joined_at = models.DateTimeField(auto_now_add=True)
    notified_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["queue_position"]

    def __str__(self):
        return f"{self.student} · {self.court} · #{self.queue_position} · {self.status}"
