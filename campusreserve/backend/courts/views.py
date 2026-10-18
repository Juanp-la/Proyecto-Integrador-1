from datetime import datetime

from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Court
from .serializers import CourtAvailabilitySerializer, CourtSerializer


class CourtListView(APIView):
    """
    HU1 — Search available courts by sport, date and time.
    HU3 — View court status clearly (available / reserved).

    GET /api/courts/?sport=soccer&date=2026-09-24&start_time=07:00&end_time=08:00

    If date/start_time/end_time are omitted, returns the plain court catalog
    with no computed status. If provided, each court gets a "status" field
    computed against existing CONFIRMED reservations for that exact slot —
    this is also where the shared-court constraint (HU5) becomes visible:
    a basketball/volleyball court reserved for one sport shows as
    "reserved" for the other, because they are the same Court row.
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        sport = request.query_params.get("sport")
        date_str = request.query_params.get("date")
        start_time_str = request.query_params.get("start_time")
        end_time_str = request.query_params.get("end_time")

        queryset = Court.objects.filter(is_active=True)
        if sport:
            queryset = queryset.filter(sport=sport)

        if date_str and start_time_str and end_time_str:
            # Local import avoids a circular import between courts <-> reservations.
            from reservations.models import Reservation

            try:
                reservation_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                start_time = datetime.strptime(start_time_str, "%H:%M").time()
                end_time = datetime.strptime(end_time_str, "%H:%M").time()
            except ValueError:
                return Response(
                    {"detail": "date must be YYYY-MM-DD, times must be HH:MM."},
                    status=400,
                )

            booked_court_ids = set(
                Reservation.objects.filter(
                    court__in=queryset,
                    reservation_date=reservation_date,
                    status="confirmed",
                    start_time__lt=end_time,
                    end_time__gt=start_time,
                ).values_list("court_id", flat=True)
            )

            data = []
            for court in queryset:
                payload = CourtSerializer(court).data
                payload["status"] = "reserved" if court.id in booked_court_ids else "available"
                data.append(payload)
            return Response(data)

        return Response(CourtSerializer(queryset, many=True).data)


class CourtDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        try:
            court = Court.objects.get(pk=pk, is_active=True)
        except Court.DoesNotExist:
            return Response({"detail": "Court not found."}, status=404)
        return Response(CourtSerializer(court).data)
