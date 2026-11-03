from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Max
from django.utils import timezone

from .models import WaitingListEntry

ACTIVE_STATUSES = ["waiting", "notified"]


@transaction.atomic
def join_waitlist(*, student, court, reservation_date, start_time, end_time):
    """HU6 — Join a waiting list for a fully booked court/date/slot."""
    from reservations.services import ActiveReservationExistsError, ensure_no_active_reservation

    try:
        ensure_no_active_reservation(student)
    except ActiveReservationExistsError as exc:
        raise ValidationError(str(exc))

    already_queued = WaitingListEntry.objects.filter(
        student=student,
        court=court,
        reservation_date=reservation_date,
        start_time=start_time,
        end_time=end_time,
        status__in=ACTIVE_STATUSES,
    ).exists()
    if already_queued:
        raise ValidationError("You are already on the waiting list for this slot.")

    current_max = WaitingListEntry.objects.filter(
        court=court,
        reservation_date=reservation_date,
        start_time=start_time,
        end_time=end_time,
        status__in=ACTIVE_STATUSES,
    ).aggregate(Max("queue_position"))["queue_position__max"] or 0

    entry = WaitingListEntry.objects.create(
        student=student,
        court=court,
        reservation_date=reservation_date,
        start_time=start_time,
        end_time=end_time,
        queue_position=current_max + 1,
        status="waiting",
    )
    return entry


@transaction.atomic
def notify_next_in_queue(*, court, reservation_date, start_time, end_time):
    """
    HU7 — Automatically notify the first student on the waiting list when
    the court/date/slot they wanted becomes available (called right after
    a reservation for that slot is cancelled).
    """
    next_entry = (
        WaitingListEntry.objects.select_for_update()
        .filter(
            court=court,
            reservation_date=reservation_date,
            start_time=start_time,
            end_time=end_time,
            status="waiting",
        )
        .order_by("queue_position")
        .first()
    )
    if not next_entry:
        return None

    window = settings.WAITLIST_CONFIRMATION_WINDOW_MINUTES
    next_entry.status = "notified"
    next_entry.notified_at = timezone.now()
    next_entry.expires_at = timezone.now() + timezone.timedelta(minutes=window)
    next_entry.save(update_fields=["status", "notified_at", "expires_at"])

    # Schedule the automatic expiration (HU8). Imported lazily so this
    # module works even in contexts where Celery isn't configured (tests).
    from .tasks import expire_waitlist_entry

    expire_waitlist_entry.apply_async(args=[next_entry.id], countdown=window * 60)

    return next_entry


@transaction.atomic
def confirm_from_waitlist(*, entry, requesting_user):
    """A notified student confirms their offered spot -> becomes a real reservation."""
    if entry.student_id != requesting_user.id:
        raise ValidationError("This waiting-list offer does not belong to you.")
    if entry.status != "notified":
        raise ValidationError("This waiting-list offer is no longer active.")
    if entry.expires_at and timezone.now() > entry.expires_at:
        raise ValidationError("This waiting-list offer has expired.")

    from reservations.services import (
        ActiveReservationExistsError,
        ReservationConflictError,
        create_reservation,
    )

    try:
        reservation = create_reservation(
            student=entry.student,
            court=entry.court,
            reservation_date=entry.reservation_date,
            start_time=entry.start_time,
            end_time=entry.end_time,
        )
    except (ReservationConflictError, ActiveReservationExistsError) as exc:
        raise ValidationError(str(exc))

    entry.status = "confirmed"
    entry.save(update_fields=["status"])
    return reservation


@transaction.atomic
def expire_and_advance(*, entry_id):
    """
    HU8 — If a notified student doesn't confirm within the time window,
    expire their offer and automatically notify the next student in line.
    """
    try:
        entry = WaitingListEntry.objects.select_for_update().get(pk=entry_id)
    except WaitingListEntry.DoesNotExist:
        return

    if entry.status != "notified":
        return  # already confirmed, or already expired by another call

    if entry.expires_at and timezone.now() < entry.expires_at:
        return  # not actually due yet (safety check)

    entry.status = "expired"
    entry.save(update_fields=["status"])

    notify_next_in_queue(
        court=entry.court,
        reservation_date=entry.reservation_date,
        start_time=entry.start_time,
        end_time=entry.end_time,
    )


@transaction.atomic
def leave_waitlist(*, entry, requesting_user):
    """
    The student leaves a waiting list (or declines an offer they were notified about).
    - Students behind them move up one position.
    - If they had been notified, the spot is offered right away to the next in line (HU7).
    """
    entry = WaitingListEntry.objects.select_for_update().get(pk=entry.pk)
    if entry.student_id != requesting_user.id:
        raise ValidationError("Esta entrada de la lista de espera no es tuya.")
    if entry.status not in ACTIVE_STATUSES:
        raise ValidationError("Ya no estás en esta lista de espera.")

    was_notified = entry.status == "notified"
    entry.status = "cancelled"
    entry.save(update_fields=["status"])

    behind = WaitingListEntry.objects.select_for_update().filter(
        court=entry.court,
        reservation_date=entry.reservation_date,
        start_time=entry.start_time,
        end_time=entry.end_time,
        status__in=ACTIVE_STATUSES,
        queue_position__gt=entry.queue_position,
    ).order_by("queue_position")
    for other in behind:
        other.queue_position -= 1
        other.save(update_fields=["queue_position"])

    if was_notified:
        notify_next_in_queue(
            court=entry.court,
            reservation_date=entry.reservation_date,
            start_time=entry.start_time,
            end_time=entry.end_time,
        )
    return entry
