from rest_framework import serializers

from reservations.serializers import ReservationSerializer

from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    reservation_detail = ReservationSerializer(source="reservation", read_only=True)

    class Meta:
        model = Notification
        fields = [
            "id", "kind", "title", "message", "reservation", "reservation_detail",
            "data", "is_read", "is_resolved", "created_at",
        ]
        read_only_fields = fields
