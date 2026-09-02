import csv
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from movie.models import Movie

CSV_NAME = 'movies_initial.csv'
NUM_MOVIES = 100  # el taller pide extraer la información de 100 películas
# Nombre del archivo ya guardado en media/movie/images/. Todas las películas
# usarán esta misma imagen (tal como pide el taller).
DEFAULT_IMAGE_NAME = 'default.jpg'
DEFAULT_IMAGE_RELATIVE_PATH = f'movie/images/{DEFAULT_IMAGE_NAME}'


class Command(BaseCommand):
    help = (
        'Puebla la tabla Movie a partir de movies_initial.csv '
        '(title, year, genre, plot), usando siempre la imagen '
        'media/movie/images/default.jpg para todas las películas.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Borra las películas existentes antes de cargar las nuevas.',
        )

    def handle(self, *args, **options):
        csv_path = settings.BASE_DIR / CSV_NAME
        if not csv_path.exists():
            self.stderr.write(self.style.ERROR(
                f'No se encontró {CSV_NAME} en {settings.BASE_DIR}. '
                'Copia el archivo ahí antes de ejecutar este comando.'
            ))
            return

        default_image_path = Path(settings.MEDIA_ROOT) / 'movie' / 'images' / DEFAULT_IMAGE_NAME
        if not default_image_path.exists():
            self.stderr.write(self.style.ERROR(
                f'No se encontró {default_image_path}. '
                'Guarda ahí la imagen default.jpg antes de ejecutar este comando.'
            ))
            return

        if options['reset']:
            deleted, _ = Movie.objects.all().delete()
            self.stdout.write(f'Se eliminaron {deleted} películas existentes.')

        created = 0
        with open(csv_path, encoding='utf-8', errors='replace') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if created >= NUM_MOVIES:
                    break

                title = (row.get('title') or '').strip()
                year_raw = (row.get('year') or '').strip()
                genre = (row.get('genre') or '').strip()
                plot = (row.get('plot') or '').strip()
                movie_type = (row.get('type') or '').strip()

                # Solo nos interesan películas (no series), con año, género
                # y descripción: son las que se pueden mostrar bien en las Cards.
                if movie_type != 'movie':
                    continue
                if not (title and year_raw and genre and plot):
                    continue
                try:
                    year = int(year_raw[:4])
                except ValueError:
                    continue

                if Movie.objects.filter(title=title).exists():
                    continue

                movie = Movie(
                    title=title,
                    description=plot[:250],
                    url='',
                    genre=genre,
                    year=year,
                )
                # Apunta directamente al archivo default.jpg que ya existe en
                # media/, sin copiarlo ni renombrarlo por cada película.
                movie.image.name = DEFAULT_IMAGE_RELATIVE_PATH
                movie.save()

                created += 1
                self.stdout.write(f'  Creada: {title} ({year}) - {genre}')

        self.stdout.write(self.style.SUCCESS(
            f'Listo. Se crearon {created} películas nuevas (de las {NUM_MOVIES} pedidas), '
            f'todas con la imagen {DEFAULT_IMAGE_RELATIVE_PATH}.'
        ))
