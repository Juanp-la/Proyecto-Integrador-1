from django.core.management.base import BaseCommand

from courts.models import Court

SEED_COURTS = [
    {
        "name": "Cancha de Fútbol 1", "sport": "soccer",
        "location": "Polideportivo Norte", "capacity": "14 jugadores",
        "surface": "Césped sintético", "image_ref": "photo-1575361204480-aadea25e6e68",
        "is_outdoor": True,
    },
    {
        "name": "Cancha de Fútbol 2", "sport": "soccer",
        "location": "Polideportivo Norte", "capacity": "14 jugadores",
        "surface": "Césped sintético", "image_ref": "photo-1575361204480-aadea25e6e68",
        "is_outdoor": True,
    },
    {
        "name": "Cancha Multiuso A — Básquet/Vóley", "sport": "basketball_volleyball",
        "location": "Polideportivo Sur", "capacity": "10 jugadores",
        "surface": "Parqué", "image_ref": "photo-1546519638-68e109498ffc",
        "is_outdoor": False,
    },
    {
        "name": "Cancha Multiuso B — Vóley", "sport": "volleyball",
        "location": "Polideportivo Sur", "capacity": "12 jugadores",
        "surface": "Parqué", "image_ref": "photo-1547347298-4074fc3086f0",
        "is_outdoor": False,
    },
]


class Command(BaseCommand):
    help = "Seeds the sports courts used in Sprint 1 + Sprint 2 (soccer, basketball/volleyball)."

    def handle(self, *args, **options):
        created = 0
        for entry in SEED_COURTS:
            court, was_created = Court.objects.get_or_create(name=entry["name"], defaults=entry)
            if not was_created and court.is_outdoor != entry["is_outdoor"]:
                court.is_outdoor = entry["is_outdoor"]
                court.save(update_fields=["is_outdoor"])
            created += int(was_created)
        self.stdout.write(self.style.SUCCESS(f"Seeded courts ({created} created)."))
