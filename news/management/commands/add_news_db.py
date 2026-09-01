from django.core.management.base import BaseCommand
from news.models import News
from datetime import datetime

class Command(BaseCommand):
    help = 'Poblar la base de datos con noticias'

    def handle(self, *args, **kwargs):
        noticias = [
            {"headline": "Nueva actualización de Django", "body": "Django 5.0 trae mejoras de seguridad.", "date": "2024-01-10"},
            {"headline": "El cine repunta en 2024", "body": "Las salas de cine ven un incremento del 20%.", "date": "2024-02-15"},
            {"headline": "Inteligencia Artificial en el cine", "body": "La IA se usa para efectos especiales.", "date": "2024-03-20"},
            {"headline": "Premios Oscar 2024", "body": "Resumen de los ganadores de la noche.", "date": "2024-03-11"},
            {"headline": "Spider-Man 4 confirmada", "body": "Tom Holland regresa como Peter Parker.", "date": "2024-04-05"}
        ]
        for n in noticias:
            date_value = datetime.strptime(n['date'], '%Y-%m-%d').date()
            News.objects.create(headline=n['headline'], body=n['body'], date=date_value)
        self.stdout.write(self.style.SUCCESS('5 Noticias cargadas exitosamente'))