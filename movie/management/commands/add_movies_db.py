import csv
import os
from django.core.management.base import BaseCommand
from django.core.files import File
from movie.models import Movie

MOVIES_TO_IMPORT = 30  # cambia este número si quieres importar más o menos

class Command(BaseCommand):
    help = 'Loads movies from netflix_titles.csv into the Movie model'

    def handle(self, *args, **options):
        csv_path = os.path.join(os.path.dirname(__file__), 'movies_initial.csv')
        default_image_path = os.path.join('media', 'movies', 'images', 'default.jpg')

        count = 0
        with open(csv_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                if count >= MOVIES_TO_IMPORT:
                    break

                if row.get('type') != 'Movie':
                    continue  # nos saltamos las series, solo queremos películas

                title = row.get('title', '').strip()
                if not title:
                    continue

                genre_field = row.get('listed_in', '')
                genre = genre_field.split(',')[0].strip() if genre_field else None

                year_field = row.get('release_year', '').strip()
                year = int(year_field) if year_field.isdigit() else None

                description = row.get('description', '').strip()
                length = row.get('duration', '').strip()

                movie = Movie(
                    title=title,
                    description=description,
                    genre=genre,
                    year=year,
                    length=length,
                    order=100 + count,
                )

                if os.path.exists(default_image_path):
                    with open(default_image_path, 'rb') as img_file:
                        movie.image.save('default.jpg', File(img_file), save=False)

                movie.save()
                count += 1

        self.stdout.write(self.style.SUCCESS(f'Imported {count} movies from netflix_titles.csv'))