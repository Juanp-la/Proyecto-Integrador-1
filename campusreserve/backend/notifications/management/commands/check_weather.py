from django.core.management.base import BaseCommand

from notifications.services import refresh_all_weather_alerts


class Command(BaseCommand):
    help = "Revisa el pronóstico y crea alertas de mal clima para reservas en canchas al aire libre."

    def handle(self, *args, **options):
        created = refresh_all_weather_alerts()
        self.stdout.write(self.style.SUCCESS(f"Alertas de clima creadas: {created}"))
