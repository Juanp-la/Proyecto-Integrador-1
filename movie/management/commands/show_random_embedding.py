import random
import numpy as np
from django.core.management.base import BaseCommand
from movie.models import Movie

class Command(BaseCommand):
    help = "Muestra el embedding de una película seleccionada al azar"

    def handle(self, *args, **kwargs):
        movies = list(Movie.objects.all())
        movie = random.choice(movies)
        embedding_vector = np.frombuffer(movie.emb, dtype=np.float32)
        self.stdout.write(f"Película: {movie.title}")
        self.stdout.write(f"Embedding (primeros 10 valores): {embedding_vector[:10]}")
        self.stdout.write(f"Dimensión total: {len(embedding_vector)}")