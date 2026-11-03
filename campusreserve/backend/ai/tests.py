"""Tests for the new features: one active reservation, leave waitlist, AI recs, weather alerts."""

from datetime import timedelta
from unittest import mock

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from courts.models import Court
from notifications.models import Notification
from reservations.models import Reservation
from waitlist.models import WaitingListEntry

User = get_user_model()
NO_AI = override_settings(AI_API_KEY="")


def fake_forecast(day, bad_hours=(), code=63, current_code=None):
    """bad_hours are Open-Meteo timestamps (rain of the PRECEDING hour): 18 = window 17:00-18:00."""
    hourly = {}
    for hour in range(0, 24):
        bad = hour in bad_hours
        hourly[f"{day.isoformat()}T{hour:02d}:00"] = {
            "temperature": 22,
            "precipitation_probability": 90 if bad else 5,
            "precipitation": 4.0 if bad else 0,
            "weather_code": code if bad else 1,
            "wind_speed": 5,
        }
    daily = {day.isoformat(): {
        "weather_code": code if bad_hours else 1, "temp_max": 27, "temp_min": 17,
        "precipitation_sum": 8 if bad_hours else 0, "precipitation_probability_max": 90 if bad_hours else 5,
    }}
    current = None
    if current_code is not None:
        current = {"time": f"{day.isoformat()}T08:00", "temperature": 21.4, "apparent_temperature": 22.1,
                   "humidity": 70, "precipitation": 0, "weather_code": current_code, "is_day": 1, "wind_speed": 4}
    return {"hourly": hourly, "daily": daily, "current": current}


class BaseCase(TestCase):
    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(username="ana@eafit.edu.co", email="ana@eafit.edu.co", password="x")
        self.other = User.objects.create_user(username="beto@eafit.edu.co", email="beto@eafit.edu.co", password="x")
        self.soccer = Court.objects.create(name="Fútbol 1", sport="soccer", location="Norte", is_outdoor=True)
        self.indoor = Court.objects.create(name="Multiuso A", sport="basketball_volleyball", location="Sur", is_outdoor=False)
        self.client = APIClient()
        self.client.force_authenticate(self.user)
        self.tomorrow = timezone.localdate() + timedelta(days=1)
        patcher = mock.patch("waitlist.tasks.expire_waitlist_entry.apply_async")
        patcher.start()
        self.addCleanup(patcher.stop)

    def book(self, court, day=None, start="17:00", end="18:00", client=None):
        return (client or self.client).post("/api/reservations/", {
            "court": court.id, "reservation_date": (day or self.tomorrow).isoformat(),
            "start_time": start, "end_time": end,
        }, format="json")


@NO_AI
class OneActiveReservationTests(BaseCase):
    def test_second_reservation_is_blocked(self):
        self.assertEqual(self.book(self.soccer).status_code, 201)
        res = self.book(self.indoor, start="09:00", end="10:00")
        self.assertEqual(res.status_code, 409)
        self.assertEqual(res.data["code"], "active_reservation_exists")

    def test_can_book_again_after_cancelling(self):
        r = self.book(self.soccer).data
        self.client.post(f"/api/reservations/{r['id']}/cancel/")
        self.assertEqual(self.book(self.indoor).status_code, 201)

    def test_past_reservation_does_not_block(self):
        Reservation.objects.create(
            student=self.user, court=self.soccer, reservation_date=timezone.localdate() - timedelta(days=2),
            start_time="10:00", end_time="11:00",
        )
        self.assertEqual(self.book(self.soccer).status_code, 201)

    def test_cannot_join_waitlist_with_active_reservation(self):
        other_client = APIClient()
        other_client.force_authenticate(self.other)
        self.book(self.indoor, client=other_client)
        self.book(self.soccer)
        res = self.client.post("/api/waitlist/", {
            "court": self.indoor.id, "reservation_date": self.tomorrow.isoformat(),
            "start_time": "17:00", "end_time": "18:00",
        }, format="json")
        self.assertEqual(res.status_code, 409)


@NO_AI
class LeaveWaitlistTests(BaseCase):
    def _join(self, user, pos):
        return WaitingListEntry.objects.create(
            student=user, court=self.soccer, reservation_date=self.tomorrow,
            start_time="17:00", end_time="18:00", queue_position=pos,
        )

    def test_leave_moves_others_up(self):
        mine = self._join(self.user, 1)
        theirs = self._join(self.other, 2)
        res = self.client.post(f"/api/waitlist/{mine.id}/leave/")
        self.assertEqual(res.status_code, 200)
        mine.refresh_from_db(); theirs.refresh_from_db()
        self.assertEqual(mine.status, "cancelled")
        self.assertEqual(theirs.queue_position, 1)
        self.assertEqual(self.client.get("/api/waitlist/mine/").data, [])

    def test_declining_notified_offer_notifies_next(self):
        mine = self._join(self.user, 1)
        mine.status = "notified"; mine.save()
        theirs = self._join(self.other, 2)
        self.client.post(f"/api/waitlist/{mine.id}/leave/")
        theirs.refresh_from_db()
        self.assertEqual(theirs.status, "notified")

    def test_cannot_leave_someone_elses_entry(self):
        theirs = self._join(self.other, 1)
        self.assertEqual(self.client.post(f"/api/waitlist/{theirs.id}/leave/").status_code, 409)


@NO_AI
class RecommendationTests(BaseCase):
    def setUp(self):
        super().setUp()
        past = timezone.localdate() - timedelta(days=3)
        for i in range(5):
            Reservation.objects.create(student=self.other, court=self.soccer,
                                       reservation_date=past - timedelta(days=i), start_time="18:00", end_time="19:00")
        Reservation.objects.create(student=self.other, court=self.indoor,
                                   reservation_date=past, start_time="07:00", end_time="08:00")

    @mock.patch("ai.weather.fetch_forecast", return_value=None)
    def test_popular_fallback_ranks_by_usage(self, _):
        data = self.client.get("/api/ai/recommendations/popular/").data
        self.assertEqual(data["source"], "fallback")
        self.assertEqual(data["items"][0]["court_id"], self.soccer.id)
        self.assertIn("18:00", data["items"][0]["peak_times"])

    @mock.patch("ai.weather.fetch_forecast", return_value=None)
    def test_quiet_returns_free_low_usage_slots(self, _):
        data = self.client.get("/api/ai/recommendations/quiet/").data
        self.assertTrue(data["items"])
        for item in data["items"]:
            self.assertEqual(item["usage_score"], 0)

    @override_settings(AI_API_KEY="test")
    @mock.patch("ai.weather.fetch_forecast", return_value=None)
    def test_popular_uses_ai_answer_and_ignores_unknown_courts(self, _):
        answer = {"summary": "La de fútbol se llena.", "items": [
            {"court_id": 9999, "reason": "inventada"},
            {"court_id": self.soccer.id, "reason": "Muy pedida en la tarde", "peak_times": ["18:00"]},
        ]}
        with mock.patch("ai.services.ask_json", return_value=answer):
            data = self.client.get("/api/ai/recommendations/popular/").data
        self.assertEqual(data["source"], "ai")
        self.assertEqual([i["court_id"] for i in data["items"]], [self.soccer.id])

    def test_quiet_skips_rainy_outdoor_slots(self):
        with mock.patch("ai.weather.fetch_forecast",
                        return_value=fake_forecast(self.tomorrow, bad_hours=range(0, 24))):
            data = self.client.get("/api/ai/recommendations/quiet/").data
        rainy = [i for i in data["items"] if i["court_id"] == self.soccer.id and i["date"] == self.tomorrow.isoformat()]
        self.assertEqual(rainy, [])


@NO_AI
class WeatherTests(BaseCase):
    def _at(self, hour):
        """Freeze 'now' at today HH:10 Bogotá time."""
        fixed = timezone.localtime().replace(hour=hour, minute=10, second=0, microsecond=0)
        return mock.patch("ai.services.timezone.localtime", return_value=fixed)

    def test_daily_report_uses_current_conditions_not_daily_worst(self):
        today = timezone.localdate()
        # Daily code = storm (Open-Meteo's daily value is the worst of the day), but right now it's clear.
        forecast = fake_forecast(today, bad_hours=[16, 17], code=95, current_code=1)
        with self._at(8), mock.patch("ai.weather.fetch_forecast", return_value=forecast):
            data = self.client.get("/api/ai/weather/today/").data
        self.assertTrue(data["available"])
        self.assertEqual(data["location"], "Medellín")
        self.assertEqual(data["condition"], "Mayormente despejado")
        self.assertEqual(data["current"]["temperature"], 21)
        # keys 16 and 17 = windows 15:00-16:00 and 16:00-17:00
        self.assertEqual(data["bad_hours"], ["15:00", "16:00"])
        self.assertEqual(len(data["hourly"]), 11)  # 08:00 ... 18:00
        self.assertNotIn("15:00", data["best_hours"])

    def test_daily_report_skips_past_hours(self):
        today = timezone.localdate()
        with self._at(14), mock.patch("ai.weather.fetch_forecast", return_value=fake_forecast(today, current_code=2)):
            data = self.client.get("/api/ai/weather/today/").data
        self.assertEqual(data["hourly"][0]["hour"], "14:00")
        self.assertTrue(all(h >= "14:00" for h in data["best_hours"]))

    def test_after_19h_reports_tomorrow(self):
        tomorrow = timezone.localdate() + timedelta(days=1)
        with self._at(20), mock.patch("ai.weather.fetch_forecast", return_value=fake_forecast(tomorrow)):
            data = self.client.get("/api/ai/weather/today/").data
        self.assertEqual(data["day_label"], "mañana")
        self.assertEqual(data["date"], tomorrow.isoformat())
        self.assertEqual(len(data["hourly"]), 13)

    @override_settings(AI_API_KEY="test")
    def test_ai_best_hours_are_limited_to_calculated_ones(self):
        today = timezone.localdate()
        answer = {"summary": "Día bueno.", "best_hours": ["09:00", "16:00", "03:00"], "advice": "Agua."}
        with self._at(8), mock.patch("ai.weather.fetch_forecast",
                                     return_value=fake_forecast(today, bad_hours=[17], code=95, current_code=0)), \
                mock.patch("ai.services.ask_json", return_value=answer):
            data = self.client.get("/api/ai/weather/today/").data
        self.assertEqual(data["source"], "ai")
        self.assertEqual(data["best_hours"], ["09:00"])  # 16:00 is stormy, 03:00 isn't a slot

    def test_hours_for_uses_preceding_hour_values(self):
        from datetime import time as t
        from ai.weather import hours_for
        f = fake_forecast(self.tomorrow, bad_hours=[18])
        h = hours_for(f, self.tomorrow, t(17), t(18))
        self.assertEqual(len(h), 1)
        self.assertEqual(h[0]["hour"], "17:00")
        self.assertEqual(h[0]["precipitation_probability"], 90)

    def test_bad_weather_creates_alert_and_cancel_from_notification(self):
        r = self.book(self.soccer).data
        with mock.patch("ai.weather.fetch_forecast",
                        return_value=fake_forecast(self.tomorrow, bad_hours=[18], code=95)):
            notes = self.client.get("/api/notifications/").data
            again = self.client.get("/api/notifications/").data  # idempotent
        self.assertEqual(len(notes), 1)
        self.assertEqual(len(again), 1)
        self.assertEqual(notes[0]["reservation"], r["id"])

        res = self.client.post(f"/api/notifications/{notes[0]['id']}/cancel-reservation/")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(Reservation.objects.get(pk=r["id"]).status, "cancelled")
        self.assertTrue(Notification.objects.get(pk=notes[0]["id"]).is_resolved)

    def test_indoor_and_good_weather_get_no_alert(self):
        self.book(self.indoor)
        with mock.patch("ai.weather.fetch_forecast",
                        return_value=fake_forecast(self.tomorrow, bad_hours=[18])):
            self.assertEqual(self.client.get("/api/notifications/").data, [])

    def test_dismiss_keeps_reservation(self):
        r = self.book(self.soccer).data
        with mock.patch("ai.weather.fetch_forecast",
                        return_value=fake_forecast(self.tomorrow, bad_hours=[18])):
            n = self.client.get("/api/notifications/").data[0]
            self.client.post(f"/api/notifications/{n['id']}/dismiss/")
            self.assertEqual(self.client.get("/api/notifications/").data, [])
        self.assertEqual(Reservation.objects.get(pk=r["id"]).status, "confirmed")
