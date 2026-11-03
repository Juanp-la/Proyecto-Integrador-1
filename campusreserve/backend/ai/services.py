"""
AI-assisted features:
  - popular_courts():       canchas más usadas (según reservas + listas de espera)
  - quiet_recommendations(): canchas y horarios poco usados y libres en los próximos días
  - daily_weather_report():  reporte del clima del día para el campus

Each function computes real numbers from the database / Open-Meteo first and
then asks the AI to choose + explain. If the AI is unavailable (no key, no
internet, bad answer) a rule-based result is returned instead, marked with
"source": "fallback" so the frontend can tell the difference.
"""

import json
from collections import Counter
from datetime import datetime, time, timedelta

from django.core.cache import cache
from django.utils import timezone

from courts.models import Court
from reservations.models import Reservation
from waitlist.models import WaitingListEntry

from . import weather
from .llm import ask_json

# Same slots offered by the frontend booking screen.
SLOTS = [
    ("06:00", "07:00"), ("07:00", "08:00"), ("08:00", "09:00"), ("09:00", "10:00"),
    ("10:00", "11:00"), ("11:00", "12:00"), ("14:00", "15:00"), ("15:00", "16:00"),
    ("16:00", "17:00"), ("17:00", "18:00"), ("18:00", "19:00"),
]
WEEKDAYS_ES = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
HISTORY_DAYS = 60
LOOKAHEAD_DAYS = 6

SYSTEM_PROMPT = (
    "Eres el asistente de CampusReserve, el sistema de reservas de canchas deportivas "
    "de la Universidad EAFIT (Medellín). Hablas en español, en tono cercano para "
    "estudiantes universitarios, con frases cortas. Solo usas los datos que te dan; "
    "no inventes canchas, horarios ni cifras."
)


def _t(s):
    return datetime.strptime(s, "%H:%M").time()


def _usage_counters():
    """Reservations (any status — a cancelled one still shows demand) + waitlist joins."""
    since = timezone.localdate() - timedelta(days=HISTORY_DAYS)
    by_court = Counter()
    by_court_slot = Counter()       # (court_id, "HH:MM")
    by_court_weekday_slot = Counter()  # (court_id, weekday, "HH:MM")
    waitlist_by_court = Counter()

    for r in Reservation.objects.filter(reservation_date__gte=since).values(
        "court_id", "reservation_date", "start_time"
    ):
        slot = r["start_time"].strftime("%H:%M")
        by_court[r["court_id"]] += 1
        by_court_slot[(r["court_id"], slot)] += 1
        by_court_weekday_slot[(r["court_id"], r["reservation_date"].weekday(), slot)] += 1

    for w in WaitingListEntry.objects.filter(reservation_date__gte=since).values(
        "court_id", "reservation_date", "start_time"
    ):
        slot = w["start_time"].strftime("%H:%M")
        waitlist_by_court[w["court_id"]] += 1
        by_court_slot[(w["court_id"], slot)] += 1
        by_court_weekday_slot[(w["court_id"], w["reservation_date"].weekday(), slot)] += 1

    return by_court, by_court_slot, by_court_weekday_slot, waitlist_by_court


# ─── Popular courts ───────────────────────────────────────────────────────────

def popular_courts():
    cached = cache.get("ai:popular")
    if cached:
        return cached

    courts = list(Court.objects.filter(is_active=True))
    by_court, by_court_slot, _, waitlist_by_court = _usage_counters()

    stats = []
    for c in courts:
        slots = sorted(
            ((slot, n) for (cid, slot), n in by_court_slot.items() if cid == c.id),
            key=lambda x: -x[1],
        )[:3]
        stats.append({
            "court_id": c.id,
            "name": c.name,
            "sport": c.get_sport_display(),
            "sport_code": c.sport,
            "location": c.location,
            "reservations": by_court[c.id],
            "waitlist_joins": waitlist_by_court[c.id],
            "peak_times": [s for s, _ in slots],
        })
    stats.sort(key=lambda s: -(s["reservations"] + s["waitlist_joins"] * 2))
    total = sum(s["reservations"] + s["waitlist_joins"] for s in stats)

    result = None
    if total > 0:
        ai = ask_json(
            SYSTEM_PROMPT,
            "Estas son las estadísticas de uso de los últimos "
            f"{HISTORY_DAYS} días (reservas y personas que se unieron a lista de espera):\n"
            f"{json.dumps(stats, ensure_ascii=False)}\n\n"
            "Elige las 3 canchas MÁS populares (las más usadas o con más demanda) y para cada una "
            "explica en 1 frase por qué es popular y en qué horas suele llenarse, con un tip "
            "para conseguirla (p. ej. reservar con anticipación). Formato:\n"
            '{"summary": "1-2 frases generales", "items": [{"court_id": 1, "reason": "...", '
            '"peak_times": ["18:00"]}]}',
        )
        result = _merge_court_items(ai, stats, limit=3)

    if result is None:
        top = [s for s in stats if s["reservations"] + s["waitlist_joins"] > 0][:3]
        result = {
            "source": "fallback",
            "summary": (
                "Estas son las canchas con más reservas en los últimos días. "
                "Resérvalas con anticipación, sobre todo en sus horas pico."
                if top else
                "Todavía no hay suficientes reservas para calcular qué canchas son las más populares."
            ),
            "items": [
                {
                    **s,
                    "reason": f"{s['reservations']} reservas y {s['waitlist_joins']} personas en lista de espera recientemente.",
                }
                for s in top
            ],
        }

    cache.set("ai:popular", result, 10 * 60)
    return result


def _merge_court_items(ai, stats, limit):
    """Keep only court_ids that exist; attach our real stats to the AI's explanation."""
    if not ai or not isinstance(ai.get("items"), list):
        return None
    by_id = {s["court_id"]: s for s in stats}
    items = []
    for it in ai["items"]:
        try:
            cid = int(it.get("court_id"))
        except (TypeError, ValueError):
            continue
        if cid in by_id and cid not in [i["court_id"] for i in items]:
            peak = [p for p in it.get("peak_times", []) if isinstance(p, str)][:3]
            items.append({**by_id[cid], "reason": str(it.get("reason", ""))[:300],
                          "peak_times": peak or by_id[cid]["peak_times"]})
    if not items:
        return None
    return {"source": "ai", "summary": str(ai.get("summary", ""))[:400], "items": items[:limit]}


# ─── Quiet (little-used) courts & times ─────────────────────────────────────────

def _quiet_candidates():
    """Free court/slot combos in the next days, scored by historical usage (lower = quieter)."""
    now = timezone.localtime()
    today = now.date()
    end_day = today + timedelta(days=LOOKAHEAD_DAYS - 1)
    courts = list(Court.objects.filter(is_active=True))
    _, by_court_slot, by_court_weekday_slot, _ = _usage_counters()

    booked = set(
        (r["court_id"], r["reservation_date"], r["start_time"].strftime("%H:%M"))
        for r in Reservation.objects.filter(
            status="confirmed", reservation_date__range=(today, end_day)
        ).values("court_id", "reservation_date", "start_time")
    )
    # How busy each date+slot is across ALL courts right now (people nearby = more crowded).
    busy_now = Counter((d, s) for (_, d, s) in booked)

    forecast = weather.fetch_forecast()
    candidates = []
    for offset in range(LOOKAHEAD_DAYS):
        day = today + timedelta(days=offset)
        for start, end in SLOTS:
            if day == today and _t(start) <= now.time():
                continue
            for c in courts:
                if (c.id, day, start) in booked:
                    continue
                rain = None
                if c.is_outdoor and forecast:
                    hours = weather.hours_for(forecast, day, _t(start), _t(end))
                    if hours:
                        rain = max(h["precipitation_probability"] for h in hours)
                        if any(weather.is_bad_hour(h) for h in hours):
                            continue  # don't recommend a rainy outdoor slot
                score = (
                    by_court_weekday_slot[(c.id, day.weekday(), start)] * 2
                    + by_court_slot[(c.id, start)]
                    + busy_now[(day, start)]
                )
                candidates.append({
                    "court_id": c.id,
                    "court_name": c.name,
                    "sport": c.get_sport_display(),
                    "sport_code": c.sport,
                    "date": day.isoformat(),
                    "weekday": WEEKDAYS_ES[day.weekday()],
                    "start_time": start,
                    "end_time": end,
                    "usage_score": score,
                    "rain_probability": rain,
                })
    # Quietest first; prefer sooner dates and keep variety between courts.
    candidates.sort(key=lambda x: (x["usage_score"], x["date"], x["start_time"]))
    diverse, seen = [], Counter()
    for cand in candidates:
        if seen[cand["court_id"]] < 4:
            diverse.append(cand)
            seen[cand["court_id"]] += 1
        if len(diverse) >= 16:
            break
    return diverse


def quiet_recommendations():
    cached = cache.get("ai:quiet")
    if cached:
        return cached

    candidates = _quiet_candidates()
    result = None
    if candidates:
        ai = ask_json(
            SYSTEM_PROMPT,
            "Estos son horarios LIBRES de los próximos días con su nivel de uso histórico "
            "(usage_score: menor = menos gente; rain_probability: % de lluvia si la cancha es al "
            "aire libre, null si es cubierta):\n"
            f"{json.dumps(candidates, ensure_ascii=False)}\n\n"
            "Elige 4 opciones tranquilas y variadas (distintas canchas o días) para alguien que "
            "quiere jugar sin multitudes. Para cada una escribe una razón breve (máx 20 palabras). "
            "Formato:\n"
            '{"summary": "1 frase", "items": [{"court_id": 1, "date": "YYYY-MM-DD", '
            '"start_time": "HH:MM", "reason": "..."}]}',
        )
        if ai and isinstance(ai.get("items"), list):
            index = {(c["court_id"], c["date"], c["start_time"]): c for c in candidates}
            items = []
            for it in ai["items"]:
                try:
                    key = (int(it.get("court_id")), str(it.get("date")), str(it.get("start_time"))[:5])
                except (TypeError, ValueError):
                    continue
                if key in index and index[key] not in items:
                    items.append({**index[key], "reason": str(it.get("reason", ""))[:200]})
            if items:
                result = {"source": "ai", "summary": str(ai.get("summary", ""))[:300], "items": items[:4]}

    if result is None:
        picks, used_courts = [], set()
        for c in candidates:  # one per court first, then fill
            if c["court_id"] not in used_courts:
                picks.append(c)
                used_courts.add(c["court_id"])
        for c in candidates:
            if len(picks) >= 4:
                break
            if c not in picks:
                picks.append(c)
        result = {
            "source": "fallback",
            "summary": "Horarios libres con poco uso en los próximos días.",
            "items": [
                {**c, "reason": "Horario con poca demanda histórica." if c["usage_score"] == 0
                 else f"Uso bajo comparado con otros horarios (nivel {c['usage_score']})."}
                for c in picks[:4]
            ],
        }

    cache.set("ai:quiet", result, 5 * 60)
    return result


def invalidate_recommendations():
    cache.delete_many(["ai:popular", "ai:quiet"])


# ─── Daily weather report ────────────────────────────────────────────────────────

def daily_weather_report():
    today = timezone.localdate()
    cache_key = f"ai:weather-report:{today.isoformat()}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    forecast = weather.fetch_forecast()
    if not forecast:
        return {
            "available": False,
            "date": today.isoformat(),
            "summary": "No se pudo consultar el clima en este momento.",
            "source": "fallback",
        }

    day = forecast["daily"].get(today.isoformat(), {})
    hours = weather.hours_for(forecast, today, time(6), time(19))
    label, icon = weather.describe(day.get("weather_code"))
    bad_hours = [h["hour"] for h in hours if weather.is_bad_hour(h)]
    good_hours = [h["hour"] for h in hours if not weather.is_bad_hour(h) and h["precipitation_probability"] < 30]

    report = {
        "available": True,
        "date": today.isoformat(),
        "condition": label,
        "icon": icon,
        "temp_max": day.get("temp_max"),
        "temp_min": day.get("temp_min"),
        "precipitation_probability_max": day.get("precipitation_probability_max"),
        "hourly": [
            {
                "hour": h["hour"],
                "temperature": h["temperature"],
                "precipitation_probability": h["precipitation_probability"],
                "icon": weather.describe(h["weather_code"])[1],
                "bad": weather.is_bad_hour(h),
            }
            for h in hours
        ],
        "bad_hours": bad_hours,
    }

    ai = ask_json(
        SYSTEM_PROMPT,
        f"Pronóstico de hoy ({WEEKDAYS_ES[today.weekday()]} {today.isoformat()}) para el campus EAFIT, "
        "por hora entre 06:00 y 19:00:\n"
        f"{json.dumps(hours, ensure_ascii=False)}\n"
        f"Resumen diario: {json.dumps(day, ensure_ascii=False)}\n\n"
        "Escribe un reporte del clima para deportistas: cómo estará el día, cuáles son las "
        "mejores horas para jugar en canchas al aire libre y una recomendación práctica "
        "(hidratación, llevar impermeable, preferir canchas cubiertas, etc.). Formato:\n"
        '{"summary": "2-3 frases", "best_hours": ["HH:00"], "advice": "1 frase"}',
    )
    if ai and ai.get("summary"):
        report.update({
            "source": "ai",
            "summary": str(ai["summary"])[:500],
            "best_hours": [h for h in ai.get("best_hours", []) if isinstance(h, str)][:5],
            "advice": str(ai.get("advice", ""))[:300],
        })
    else:
        rain_text = (
            f"Hay riesgo de lluvia fuerte a las {', '.join(bad_hours[:4])}."
            if bad_hours else "No se espera lluvia fuerte durante el día."
        )
        report.update({
            "source": "fallback",
            "summary": f"{label} hoy, entre {day.get('temp_min')}°C y {day.get('temp_max')}°C. {rain_text}",
            "best_hours": good_hours[:5],
            "advice": "Si llueve, prefiere las canchas cubiertas." if bad_hours
                      else "Buen día para jugar al aire libre; lleva agua.",
        })

    cache.set(cache_key, report, 60 * 60)
    return report
