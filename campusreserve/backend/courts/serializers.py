from rest_framework import serializers

from .models import Court


class CourtSerializer(serializers.ModelSerializer):
    class Meta:
        model = Court
        fields = [
            "id", "name", "sport", "location", "capacity", "surface",
            "image_ref", "is_active",
        ]


class CourtAvailabilitySerializer(CourtSerializer):
    """Adds the computed status (HU3) for a requested date/time slot."""

    status = serializers.CharField()

    class Meta(CourtSerializer.Meta):
        fields = CourtSerializer.Meta.fields + ["status"]
