from django.conf import settings
from django.db import models


class Notification(models.Model):
    """
    In-app notification. Currently used for bad-weather alerts on a student's
    reservation (with the option to cancel it from the notification).
    """

    KIND_CHOICES = [
        ("weather_alert", "Alerta de clima"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications"
    )
    kind = models.CharField(max_length=30, choices=KIND_CHOICES)
    title = models.CharField(max_length=160)
    message = models.TextField()
    reservation = models.ForeignKey(
        "reservations.Reservation",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="notifications",
    )
    # Snapshot of the forecast that triggered the alert (shown in the UI).
    data = models.JSONField(default=dict, blank=True)
    is_read = models.BooleanField(default=False)
    # True once the student acted on it (cancelled or chose to keep the reservation).
    is_resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user} · {self.kind} · {self.title}"
