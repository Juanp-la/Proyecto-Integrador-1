import os
import pandas as pd
from django.core.management.base import BaseCommand
from django.conf import settings
from movie.models import Movie


class Command(BaseCommand):
    help = 'Puebla la base de datos de peliculas a partir de movies_initial.csv'

    def handle(self, *args, **options):
        # Ruta esperada del CSV: dentro de esta misma carpeta (movie/management/commands/)
        csv_path = os.path.join(os.path.dirname(__file__), 'movies_initial.csv')

        if not os.path.exists(csv_path):
            self.stdout.write(self.style.ERROR(
                f'No se encontro el archivo: {csv_path}\n'
                'Coloca movies_initial.csv en movie/management/commands/'
            ))
            return

        df = pd.read_csv(csv_path)

        # Detecta el nombre real de cada columna sin importar mayusculas/variantes
        def find_col(possible_names):
            for col in df.columns:
                if col.strip().lower() in possible_names:
                    return col
            return None

        title_col = find_col(['title', 'name'])
        genre_col = find_col(['genre', 'genres'])
        year_col = find_col(['year', 'release year', 'release_year'])
        desc_col = find_col(['description', 'plot', 'overview', 'summary'])

        if not title_col:
            self.stdout.write(self.style.ERROR(
                'No se encontro una columna de titulo en el CSV. '
                f'Columnas disponibles: {list(df.columns)}'
            ))
            return

        # Limita a 100 peliculas como pide el taller
        df = df.head(100)

        created_count = 0
        for _, row in df.iterrows():
            title = str(row[title_col]).strip()
            genre = str(row[genre_col]).strip() if genre_col and pd.notna(row[genre_col]) else ''
            description = str(row[desc_col]).strip() if desc_col and pd.notna(row[desc_col]) else ''
            description = description[:250]  # el modelo limita a 250 caracteres

            year = None
            if year_col and pd.notna(row[year_col]):
                try:
                    year = int(float(row[year_col]))
                except (ValueError, TypeError):
                    year = None

            movie = Movie(
                title=title[:100],
                description=description,
                genre=genre[:250],
                year=year,
            )
            # Asigna la imagen por defecto (debe existir en media/movie/images/default.jpg)
            movie.image.name = 'movie/images/default.jpg'
            movie.save()
            created_count += 1

        self.stdout.write(self.style.SUCCESS(
            f'{created_count} peliculas agregadas a la base de datos.'
        ))
