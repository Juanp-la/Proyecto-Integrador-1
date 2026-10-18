from django.core.exceptions import ValidationError
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from reservations.serializers import ReservationSerializer

from .models import WaitingListEntry
from .serializers import JoinWaitlistSerializer, WaitingListEntrySerializer
from .services import confirm_from_waitlist, join_waitlist


class MyWaitlistView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        entries = WaitingListEntry.objects.filter(
            student=request.user, status__in=["waiting", "notified"]
        )
        return Response(WaitingListEntrySerializer(entries, many=True).data)


class JoinWaitlistView(APIView):
    """HU6 — Join a waiting list for a fully booked court/date/slot."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = JoinWaitlistSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            entry = join_waitlist(student=request.user, **serializer.validated_data)
        except ValidationError as exc:
            return Response({"detail": str(exc)}, status=409)

        return Response(WaitingListEntrySerializer(entry).data, status=201)


class ConfirmWaitlistOfferView(APIView):
    """Student confirms a notified waiting-list offer (HU7 -> becomes a reservation)."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            entry = WaitingListEntry.objects.get(pk=pk)
        except WaitingListEntry.DoesNotExist:
            return Response({"detail": "Waiting-list entry not found."}, status=404)

        try:
            reservation = confirm_from_waitlist(entry=entry, requesting_user=request.user)
        except ValidationError as exc:
            return Response({"detail": str(exc)}, status=409)

        return Response(ReservationSerializer(reservation).data, status=201)
