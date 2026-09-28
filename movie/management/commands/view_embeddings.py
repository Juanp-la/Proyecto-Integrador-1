import numpy as np
import random
from django.core.management.base import BaseCommand
from movie.models import Movie

class Command(BaseCommand):
    help = 'View embeddings for a random movie'

    def handle(self, *args, **kwargs):
        movies = list(Movie.objects.all())
        if not movies:
            return
        
        movie = random.choice(movies)
        embedding_vector = np.frombuffer(movie.emb, dtype=np.float32)
        
        self.stdout.write(self.style.SUCCESS(f"🎬 Película seleccionada: {movie.title}"))
        self.stdout.write(f"Vectores (primeros 5 valores): {embedding_vector[:5]}")