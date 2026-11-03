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

LOCATION_NAME = "Medellín"
GOOD_RAIN_PROBABILITY = 40  # below this %, an hour counts as a good time to play outside


def _r(x):
    return round(x) if isinstance(x, (int, float)) else x


def daily_weather_report():
    """
    Weather report for Medellín (EAFIT campus).

    The numbers are computed here from Open-Meteo; the AI only writes the text.
    - "Now" uses Open-Meteo's *current* conditions (not the daily code, which
      is the most severe condition of the whole day: in Medellín that's almost
      always an afternoon storm, so it looked stormy even when it was sunny).
    - Only the hours that are still ahead are analysed. After 19:00 the report
      switches to tomorrow.
    """
    now = timezone.localtime()
    is_tomorrow = now.hour >= 19
    target = now.date() + timedelta(days=1) if is_tomorrow else now.date()
    cache_key = f"ai:weather-report:{now.date().isoformat()}:{now.hour}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    forecast = weather.fetch_forecast()
    if not forecast:
        return {
            "available": False,
            "location": LOCATION_NAME,
            "date": target.isoformat(),
            "summary": "No se pudo consultar el clima en este momento.",
            "source": "fallback",
        }

    day = forecast["daily"].get(target.isoformat(), {})
    first_hour = 6 if is_tomorrow else max(6, now.hour)
    hours = weather.hours_for(forecast, target, time(min(first_hour, 18)), time(19))

    def label(code):
        return weather.describe(code)[0]

    bad_hours = [h["hour"] for h in hours if weather.is_bad_hour(h)]
    good_hours = [
        h["hour"] for h in hours
        if not weather.is_bad_hour(h) and h["precipitation_probability"] < GOOD_RAIN_PROBABILITY
    ]
    if not good_hours:  # rainy day: suggest the least rainy hours that aren't storms
        calmer = sorted((h for h in hours if not weather.is_bad_hour(h)),
                        key=lambda h: h["precipitation_probability"])
        good_hours = sorted(h["hour"] for h in calmer[:3])
    rain_ahead = max((h["precipitation_probability"] for h in hours), default=0)

    # Headline: current conditions today; most common daytime condition tomorrow.
    current = forecast.get("current") if not is_tomorrow else None
    if current and current.get("weather_code") is not None:
        cond_label, cond_icon = weather.describe(current["weather_code"])
        if current.get("is_day") == 0 and current["weather_code"] in (0, 1):
            cond_icon = "🌙"
    else:
        codes = Counter(h["weather_code"] for h in hours)
        dominant = codes.most_common(1)[0][0] if codes else day.get("weather_code")
        cond_label, cond_icon = weather.describe(dominant)

    report = {
        "available": True,
        "location": LOCATION_NAME,
        "date": target.isoformat(),
        "day_label": "mañana" if is_tomorrow else "hoy",
        "condition": cond_label,
        "icon": cond_icon,
        "current": (
            {
                "temperature": _r(current.get("temperature")),
                "apparent_temperature": _r(current.get("apparent_temperature")),
                "humidity": _r(current.get("humidity")),
                "condition": cond_label,
                "icon": cond_icon,
            }
            if current else None
        ),
        "temp_max": _r(day.get("temp_max")),
        "temp_min": _r(day.get("temp_min")),
        # Max rain chance in the hours that are still ahead (not the whole day).
        "precipitation_probability_max": rain_ahead,
        "hourly": [
            {
                "hour": h["hour"],
                "temperature": _r(h["temperature"]),
                "precipitation_probability": h["precipitation_probability"],
                "icon": weather.describe(h["weather_code"])[1],
                "condition": label(h["weather_code"]),
                "bad": weather.is_bad_hour(h),
            }
            for h in hours
        ],
        "bad_hours": bad_hours,
    }

    ai_input = {
        "ciudad": f"{LOCATION_NAME} (campus EAFIT)",
        "reporte_para": report["day_label"],
        "fecha": target.isoformat(),
        "hora_actual": now.strftime("%H:%M"),
        "ahora": (
            {
                "condicion": cond_label,
                "temperatura_c": report["current"]["temperature"],
                "sensacion_termica_c": report["current"]["apparent_temperature"],
                "humedad_pct": report["current"]["humidity"],
            }
            if report["current"] else None
        ),
        "temperatura_min_c": report["temp_min"],
        "temperatura_max_c": report["temp_max"],
        "horas": [
            {
                "franja": f"{h['hour']}-{int(h['hour'][:2]) + 1:02d}:00",
                "condicion": label(h["weather_code"]),
                "temperatura_c": _r(h["temperature"]),
                "prob_lluvia_pct": h["precipitation_probability"],
                "lluvia_mm": h["precipitation"],
            }
            for h in hours
        ],
        "horas_buenas_calculadas": good_hours,
        "horas_con_mal_clima": bad_hours,
    }
    ai = ask_json(
        SYSTEM_PROMPT,
        "Datos REALES del pronóstico (Open-Meteo) para jugar en canchas al aire libre:\n"
        f"{json.dumps(ai_input, ensure_ascii=False)}\n\n"
        "Escribe el reporte del clima de " + report["day_label"] + " en Medellín. Reglas:\n"
        "- Habla solo de las franjas listadas (son las que faltan del día); no menciones horas que ya pasaron.\n"
        "- Usa exactamente las cifras dadas (temperaturas y % de lluvia); no inventes datos.\n"
        "- best_hours debe ser un subconjunto de horas_buenas_calculadas (formato HH:00).\n"
        "- Si hay horas_con_mal_clima, menciónalas.\n"
        "Formato:\n"
        '{"summary": "2-3 frases", "best_hours": ["HH:00"], "advice": "1 frase práctica"}',
        temperature=0.2,
    )
    if ai and isinstance(ai.get("summary"), str) and ai["summary"].strip():
        allowed = set(good_hours)
        best = [h for h in ai.get("best_hours", []) if isinstance(h, str) and h[:5] in allowed]
        report.update({
            "source": "ai",
            "summary": ai["summary"].strip()[:500],
            "best_hours": [h[:5] for h in best][:5] or good_hours[:5],
            "advice": str(ai.get("advice", ""))[:300],
        })
    else:
        report.update({"source": "fallback", **_fallback_weather_text(report, good_hours, bad_hours)})

    cache.set(cache_key, report, 20 * 60)
    return report


def _fallback_weather_text(report, good_hours, bad_hours):
    parts = []
    cur = report.get("current")
    if cur:
        parts.append(
            f"Ahora en {LOCATION_NAME}: {cur['condition'].lower()}, {cur['temperature']}°C "
            f"(sensación {cur['apparent_temperature']}°C)."
        )
    parts.append(f"Temperatura de {report['day_label']} entre {report['temp_min']}°C y {report['temp_max']}°C.")
    if not report["hourly"]:
        parts.append("Ya no quedan horarios de cancha por hoy.")
    elif bad_hours:
        parts.append(f"Hay riesgo de lluvia fuerte o tormenta a las {', '.join(bad_hours[:4])}.")
    else:
        parts.append(f"Probabilidad de lluvia máxima de {report['precipitation_probability_max']}% en lo que queda del día.")
    return {
        "summary": " ".join(parts),
        "best_hours": good_hours[:5],
        "advice": (
            "Si llueve, prefiere las canchas cubiertas." if bad_hours
            else "Buen momento para jugar al aire libre; lleva agua."
        ),
    }
