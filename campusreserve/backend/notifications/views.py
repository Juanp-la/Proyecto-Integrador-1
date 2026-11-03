import logging

from django.core.exceptions import ValidationError
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from reservations.services import cancel_reservation

from .models import Notification
from .serializers import NotificationSerializer
from .services import refresh_weather_alerts

logger = logging.getLogger(__name__)


class MyNotificationsView(APIView):
    """
    GET /api/notifications/ — pending notifications of the student.
    Also checks the forecast on the spot, so weather alerts appear even if
    the Celery beat scheduler isn't running.
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            refresh_weather_alerts(request.user)
        except Exception:
            logger.exception("Could not refresh weather alerts")
        qs = Notification.objects.filter(user=request.user, is_resolved=False).select_related(
            "reservation__court"
        )
        return Response(NotificationSerializer(qs, many=True).data)


class _OwnNotificationMixin:
    def get_notification(self, request, pk):
        try:
            return Notification.objects.get(pk=pk, user=request.user)
        except Notification.DoesNotExist:
            return None


class DismissNotificationView(_OwnNotificationMixin, APIView):
    """POST /api/notifications/<id>/dismiss/ — "Mantener reserva" / ocultar el aviso."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        n = self.get_notification(request, pk)
        if not n:
            return Response({"detail": "Notification not found."}, status=404)
        n.is_read = True
        n.is_resolved = True
        n.save(update_fields=["is_read", "is_resolved"])
        return Response(NotificationSerializer(n).data)


class CancelReservationFromNotificationView(_OwnNotificationMixin, APIView):
    """POST /api/notifications/<id>/cancel-reservation/ — cancela la reserva por mal clima."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        n = self.get_notification(request, pk)
        if not n:
            return Response({"detail": "Notification not found."}, status=404)
        if not n.reservation:
            return Response({"detail": "Esta notificación no tiene una reserva asociada."}, status=400)
        try:
            cancel_reservation(reservation=n.reservation, requesting_user=request.user)
        except ValidationError as exc:
            return Response({"detail": exc.messages[0]}, status=403)
        n.refresh_from_db()
        n.is_read = True
        n.is_resolved = True
        n.save(update_fields=["is_read", "is_resolved"])
        return Response(NotificationSerializer(n).data)
