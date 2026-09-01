import csv
import os
from django.core.management.base import BaseCommand
from movie.models import Movie
from django.conf import settings

class Command(BaseCommand):
    help = 'Poblar la base de datos con películas'

    def handle(self, *args, **kwargs):
        # Busca el archivo en la raíz del proyecto
        file_path = os.path.join(settings.BASE_DIR, 'movies_initial.csv')
        
        with open(file_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                Movie.objects.create(
                    title=row['title'],
                    description=row['description'],
                    genre=row['genre'],
                    year=row['year'],
                    image='movie/images/default.jpg'
                )
                
        self.stdout.write(self.style.SUCCESS('¡10 Películas cargadas exitosamente!'))