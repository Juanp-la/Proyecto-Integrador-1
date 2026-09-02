import csv
import os
from django.core.management.base import BaseCommand
from movie.models import Movie

class Command(BaseCommand):
    help = 'Carga películas desde movies_initial.csv a la base de datos'

    def handle(self, *args, **kwargs):
        csv_path = os.path.join(os.path.dirname(__file__), 'movies_initial.csv')

        count = 0
        with open(csv_path, encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                if count >= 100:
                    break

                title = row.get('title', '').strip()
                if not title:
                    continue

                description = row.get('plot', '').strip()
                genre = row.get('genre', '').strip()
                year_value = row.get('year', '').strip()

                try:
                    year = int(year_value)
                except (ValueError, TypeError):
                    year = None

                movie = Movie(
                    title=title,
                    description=description[:250],
                    genre=genre[:250],
                    year=year,
                    image='movie/images/default.jpg'
                )
                movie.save()
                count += 1

        self.stdout.write(self.style.SUCCESS(f'Se cargaron {count} películas exitosamente'))