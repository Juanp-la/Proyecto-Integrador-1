from datetime import time, timedelta
from unittest import mock

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from courts.models import Court
from reservations.models import Reservation


class IsActiveFieldTests(TestCase):
    """The frontend relies on the server's is_active (Bogotá time), not on the user's clock."""

    def setUp(self):
        self.user = get_user_model().objects.create_user(username="a@eafit.edu.co", password="x")
        self.court = Court.objects.create(name="F1", sport="soccer", location="Norte")
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def _mine(self):
        return {r["id"]: r["is_active"] for r in self.client.get("/api/reservations/mine/").data}

    def test_is_active_today_future_and_past(self):
        now = timezone.localtime().replace(hour=14, minute=10)
        today = now.date()
        later = Reservation.objects.create(student=self.user, court=self.court, reservation_date=today,
                                           start_time=time(15), end_time=time(16))
        earlier = Reservation.objects.create(student=self.user, court=self.court, reservation_date=today,
                                             start_time=time(9), end_time=time(10))
        tomorrow = Reservation.objects.create(student=self.user, court=self.court,
                                              reservation_date=today + timedelta(days=1),
                                              start_time=time(9), end_time=time(10))
        with mock.patch("django.utils.timezone.localtime", return_value=now):
            mine = self._mine()
        self.assertTrue(mine[later.id])
        self.assertFalse(mine[earlier.id])
        self.assertTrue(mine[tomorrow.id])

    def test_new_reservation_is_listed_as_active(self):
        day = (timezone.localdate() + timedelta(days=1)).isoformat()
        res = self.client.post("/api/reservations/", {"court": self.court.id, "reservation_date": day,
                                                      "start_time": "17:00", "end_time": "18:00"}, format="json")
        self.assertEqual(res.status_code, 201)
        self.assertTrue(res.data["is_active"])
        self.assertEqual(self._mine(), {res.data["id"]: True})
