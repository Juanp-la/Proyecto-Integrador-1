from django.core.exceptions import ValidationError
from django.db import transaction

from .models import Reservation


class ReservationConflictError(Exception):
    """Raised when the requested court is already booked for that slot."""


class ActiveReservationExistsError(Exception):
    """Raised when the student already holds an active (upcoming) reservation."""

    code = "active_reservation_exists"


def active_reservations_for(student):
    """
    Confirmed reservations of `student` that haven't finished yet
    (today with end_time still ahead, or any future date).
    """
    from django.db.models import Q
    from django.utils import timezone

    now = timezone.localtime()
    return Reservation.objects.filter(student=student, status="confirmed").filter(
        Q(reservation_date__gt=now.date())
        | Q(reservation_date=now.date(), end_time__gt=now.time())
    )


def ensure_no_active_reservation(student):
    """Una reserva a la vez: blocks a new booking while another one is still active."""
    active = active_reservations_for(student).select_related("court").first()
    if active:
        raise ActiveReservationExistsError(
            "Solo puedes tener una reserva activa a la vez. Ya tienes "
            f"{active.court.name} el {active.reservation_date:%Y-%m-%d} a las "
            f"{active.start_time:%H:%M}. Cancélala o espera a que termine para reservar otra."
        )


@transaction.atomic
def create_reservation(*, student, court, reservation_date, start_time, end_time):
    """
    HU2 — Reserve a court.
    HU5 — Shared-court constraint: because a shared physical court (e.g.
    basketball/volleyball) is modeled as a single Court row, this overlap
    check against `court=court` already blocks the other sport for the
    same slot — no extra logic needed.
    Also enforces "una reserva a la vez" (one active reservation per student).
    """
    # Lock the student's row so two simultaneous requests can't both pass the check.
    type(student).objects.select_for_update().filter(pk=student.pk).first()
    ensure_no_active_reservation(student)

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
    from ai.services import invalidate_recommendations

    transaction.on_commit(invalidate_recommendations)
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

    # Any pending weather alert for this reservation is now resolved.
    from notifications.models import Notification

    Notification.objects.filter(reservation=reservation, is_resolved=False).update(
        is_resolved=True
    )

    from ai.services import invalidate_recommendations

    transaction.on_commit(invalidate_recommendations)

    # Local import avoids a circular import between reservations <-> waitlist.
    from waitlist.services import notify_next_in_queue

    notify_next_in_queue(
        court=reservation.court,
        reservation_date=reservation.reservation_date,
        start_time=reservation.start_time,
        end_time=reservation.end_time,
    )

    return reservation
