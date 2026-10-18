from django.core.exceptions import ValidationError
from django.db import transaction

from .models import Reservation


class ReservationConflictError(Exception):
    """Raised when the requested court is already booked for that slot."""


@transaction.atomic
def create_reservation(*, student, court, reservation_date, start_time, end_time):
    """
    HU2 — Reserve a court.
    HU5 — Shared-court constraint: because a shared physical court (e.g.
    basketball/volleyball) is modeled as a single Court row, this overlap
    check against `court=court` already blocks the other sport for the
    same slot — no extra logic needed.
    """
    conflict_exists = Reservation.objects.select_for_update().filter(
        court=court,
        reservation_date=reservation_date,
        status="confirmed",
        start_time__lt=end_time,
        end_time__gt=start_time,
    ).exists()

    if conflict_exists:
        raise ReservationConflictError(
            "This court is already reserved for the selected date and time."
        )

    reservation = Reservation.objects.create(
        student=student,
        court=court,
        reservation_date=reservation_date,
        start_time=start_time,
        end_time=end_time,
        status="confirmed",
    )
    return reservation


@transaction.atomic
def cancel_reservation(*, reservation, requesting_user):
    """
    HU4 — Cancel a reservation. Only the owner can cancel it.
    On success, triggers the waiting-list notification flow (HU7) for the
    freed-up court/date/slot, if a waiting list exists.
    """
    if reservation.student_id != requesting_user.id:
        raise ValidationError("You can only cancel your own reservations.")

    if reservation.status == "cancelled":
        return reservation

    from django.utils import timezone

    reservation.status = "cancelled"
    reservation.cancelled_at = timezone.now()
    reservation.save(update_fields=["status", "cancelled_at"])

    # Local import avoids a circular import between reservations <-> waitlist.
    from waitlist.services import notify_next_in_queue

    notify_next_in_queue(
        court=reservation.court,
        reservation_date=reservation.reservation_date,
        start_time=reservation.start_time,
        end_time=reservation.end_time,
    )

    return reservation
