import random
from datetime import time, timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from courts.models import Court
from reservations.models import Reservation
from waitlist.models import WaitingListEntry

# Weighted so there's a clear "popular" pattern (evenings, soccer) and quiet ones (mornings).
SLOT_WEIGHTS = {
    6: 1, 7: 2, 8: 1, 9: 1, 10: 2, 11: 3, 14: 2, 15: 3, 16: 5, 17: 8, 18: 9,
}


class Command(BaseCommand):
    help = (
        "Crea reservas PASADAS de usuarios demo para que las recomendaciones de canchas "
        "populares / poco usadas tengan datos. No afecta reservas futuras."
    )

    def add_arguments(self, parser):
        parser.add_argument("--count", type=int, default=120)

    def handle(self, *args, **opts):
        User = get_user_model()
        courts = list(Court.objects.filter(is_active=True))
        if not courts:
            self.stderr.write("No hay canchas. Corre primero: python manage.py seed_courts")
            return

        users = []
        for i in range(1, 9):
            email = f"demo{i}@eafit.edu.co"
            u, created = User.objects.get_or_create(
                username=email, defaults={"email": email, "first_name": "Demo", "last_name": str(i)}
            )
            if created:
                u.set_password("CampusReserve123!")
                u.save()
            users.append(u)

        # Soccer courts get more demand than the rest.
        court_weights = [4 if c.sport == "soccer" else 2 if c.sport == "basketball_volleyball" else 1 for c in courts]
        hours, hour_weights = list(SLOT_WEIGHTS), list(SLOT_WEIGHTS.values())
        rng = random.Random(42)
        today = timezone.localdate()
        created = 0
        for _ in range(opts["count"]):
            court = rng.choices(courts, weights=court_weights)[0]
            hour = rng.choices(hours, weights=hour_weights)[0]
            day = today - timedelta(days=rng.randint(1, 45))
            if Reservation.objects.filter(
                court=court, reservation_date=day, start_time=time(hour), status="confirmed"
            ).exists():
                # Fully booked slot -> someone joined the waiting list (demand signal).
                WaitingListEntry.objects.create(
                    student=rng.choice(users), court=court, reservation_date=day,
                    start_time=time(hour), end_time=time(hour + 1), queue_position=1, status="expired",
                )
                continue
            Reservation.objects.create(
                student=rng.choice(users), court=court, reservation_date=day,
                start_time=time(hour), end_time=time(hour + 1),
                status=rng.choices(["confirmed", "cancelled"], weights=[85, 15])[0],
            )
            created += 1

        from ai.services import invalidate_recommendations

        invalidate_recommendations()
        self.stdout.write(self.style.SUCCESS(f"Reservas demo creadas: {created}"))
