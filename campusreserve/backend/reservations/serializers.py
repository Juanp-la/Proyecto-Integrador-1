from rest_framework import serializers

from courts.models import Court
from courts.serializers import CourtSerializer

from .models import Reservation


class ReservationSerializer(serializers.ModelSerializer):
    court_detail = CourtSerializer(source="court", read_only=True)

    class Meta:
        model = Reservation
        fields = [
            "id", "court", "court_detail", "reservation_date", "start_time",
            "end_time", "status", "created_at", "cancelled_at",
        ]
        read_only_fields = ["status", "created_at", "cancelled_at"]


class CreateReservationSerializer(serializers.Serializer):
    """HU2 — input payload for creating a reservation."""

    court = serializers.PrimaryKeyRelatedField(queryset=Court.objects.filter(is_active=True))
    reservation_date = serializers.DateField()
    start_time = serializers.TimeField()
    end_time = serializers.TimeField()

    def validate(self, attrs):
        if attrs["start_time"] >= attrs["end_time"]:
            raise serializers.ValidationError("start_time must be before end_time.")
        return attrs
