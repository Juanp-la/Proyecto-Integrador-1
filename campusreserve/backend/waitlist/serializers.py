from rest_framework import serializers

from courts.models import Court
from courts.serializers import CourtSerializer

from .models import WaitingListEntry


class WaitingListEntrySerializer(serializers.ModelSerializer):
    court_detail = CourtSerializer(source="court", read_only=True)

    class Meta:
        model = WaitingListEntry
        fields = [
            "id", "court", "court_detail", "reservation_date", "start_time",
            "end_time", "queue_position", "status", "joined_at", "notified_at",
            "expires_at",
        ]
        read_only_fields = ["queue_position", "status", "joined_at", "notified_at", "expires_at"]


class JoinWaitlistSerializer(serializers.Serializer):
    court = serializers.PrimaryKeyRelatedField(queryset=Court.objects.filter(is_active=True))
    reservation_date = serializers.DateField()
    start_time = serializers.TimeField()
    end_time = serializers.TimeField()
