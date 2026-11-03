import json
import logging

from django.contrib.auth import get_user_model

from ai import weather
from ai.llm import ask_json
from ai.services import SYSTEM_PROMPT
from reservations.services import active_reservations_for

from .models import Notification

logger = logging.getLogger(__name__)


def refresh_weather_alerts(user):
    """
    Checks the forecast for each upcoming reservation of `user` on an outdoor
    court and creates ONE weather_alert notification per reservation when bad
    weather is expected. Safe to call often (idempotent; forecast is cached).
    Returns the number of new alerts created.
    """
    reservations = list(
        active_reservations_for(user).filter(court__is_outdoor=True).select_related("court")
    )
    if not reservations:
        return 0

    already_alerted = set(
        Notification.objects.filter(
            user=user, kind="weather_alert", reservation__in=reservations
        ).values_list("reservation_id", flat=True)
    )
    pending = [r for r in reservations if r.id not in already_alerted]
    if not pending:
        return 0

    forecast = weather.fetch_forecast()
    if not forecast:
        return 0

    created = 0
    for r in pending:
        hours = weather.hours_for(forecast, r.reservation_date, r.start_time, r.end_time)
        bad = weather.bad_weather_summary(hours)
        if not bad:
            continue

        when = f"{r.reservation_date:%Y-%m-%d} de {r.start_time:%H:%M} a {r.end_time:%H:%M}"
        message = (
            f"Se pronostica {bad['label'].lower()} cerca de las {bad['hour']} "
            f"({bad['precipitation_probability']}% de probabilidad de lluvia) en {r.court.name}, "
            f"para tu reserva del {when}. Puedes cancelarla o mantenerla."
        )
        ai = ask_json(
            SYSTEM_PROMPT,
            "Un estudiante tiene esta reserva en una cancha al aire libre y se pronostica mal clima:\n"
            + json.dumps({"cancha": r.court.name, "cuando": when, "pronostico": bad}, ensure_ascii=False)
            + "\nEscribe un aviso corto (máx 35 palabras) que explique el riesgo y le sugiera "
            "cancelar o cambiar a una cancha cubierta. Formato: {\"message\": \"...\"}",
        )
        if ai and isinstance(ai.get("message"), str) and ai["message"].strip():
            message = ai["message"].strip()[:400]

        Notification.objects.create(
            user=user,
            kind="weather_alert",
            reservation=r,
            title=f"{bad['icon']} Mal clima para tu reserva en {r.court.name}",
            message=message,
            data={**bad, "source": "ai" if ai else "fallback"},
        )
        created += 1
    return created


def refresh_all_weather_alerts():
    """Used by the Celery beat task / management command for every student."""
    from reservations.models import Reservation

    total = 0
    user_ids = (
        Reservation.objects.filter(status="confirmed", court__is_outdoor=True)
        .values_list("student_id", flat=True)
        .distinct()
    )
    for user in get_user_model().objects.filter(id__in=user_ids):
        try:
            total += refresh_weather_alerts(user)
        except Exception:  # one bad user shouldn't stop the batch
            logger.exception("Weather alert check failed for user %s", user.pk)
    return total
