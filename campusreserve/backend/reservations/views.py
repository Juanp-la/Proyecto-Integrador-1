from django.core.exceptions import ValidationError
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Reservation
from .serializers import CreateReservationSerializer, ReservationSerializer
from .services import ReservationConflictError, cancel_reservation, create_reservation


class MyReservationsView(APIView):
    """List the requesting student's own reservations."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        reservations = Reservation.objects.filter(student=request.user)
        return Response(ReservationSerializer(reservations, many=True).data)


class ReservationCreateView(APIView):
    """HU2 — Reserve a court."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = CreateReservationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            reservation = create_reservation(
                student=request.user,
                **serializer.validated_data,
            )
        except ReservationConflictError as exc:
            return Response({"detail": str(exc)}, status=409)

        return Response(ReservationSerializer(reservation).data, status=201)


class ReservationCancelView(APIView):
    """HU4 — Cancel a reservation."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            reservation = Reservation.objects.get(pk=pk)
        except Reservation.DoesNotExist:
            return Response({"detail": "Reservation not found."}, status=404)

        try:
            reservation = cancel_reservation(reservation=reservation, requesting_user=request.user)
        except ValidationError as exc:
            return Response({"detail": str(exc)}, status=403)

        return Response(ReservationSerializer(reservation).data)
