from rest_framework import serializers

from courts.models import Court
from courts.serializers import CourtSerializer

from .models import Reservation


class ReservationSerializer(serializers.ModelSerializer):
    court_detail = CourtSerializer(source="court", read_only=True)
    # Computed on the server (Bogotá time) so the frontend doesn't depend on
    # the user's computer clock/timezone to decide what counts as "active".
    is_active = serializers.SerializerMethodField()

    class Meta:
        model = Reservation
        fields = [
            "id", "court", "court_detail", "reservation_date", "start_time",
            "end_time", "status", "created_at", "cancelled_at", "is_active",
        ]
        read_only_fields = ["status", "created_at", "cancelled_at"]

    def get_is_active(self, obj):
        from django.utils import timezone

        if obj.status != "confirmed":
            return False
        now = timezone.localtime()
        if obj.reservation_date != now.date():
            return obj.reservation_date > now.date()
        return obj.end_time > now.time()


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
