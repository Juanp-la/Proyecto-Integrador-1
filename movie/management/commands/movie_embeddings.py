import numpy as np
import re
from django.core.management.base import BaseCommand
from movie.models import Movie

class Command(BaseCommand):
    help = 'Generate and store deterministic smart mock embeddings'

    def handle(self, *args, **kwargs):
        movies = Movie.objects.all()
        self.stdout.write(f"Found {movies.count()} movies in the database")

        def get_smart_vector(text):
            vec = np.zeros(1536, dtype=np.float32)
            words = re.findall(r'\w+', text.lower())
            for w in words:
                # Matemática fija: suma el valor de cada letra para un índice exacto
                idx = sum(ord(c) for c in w) % 1536
                vec[idx] += 1.0
            return vec

        for movie in movies:
            embedding_array = get_smart_vector(movie.description)
            movie.emb = embedding_array.tobytes()
            movie.save()
            self.stdout.write(self.style.SUCCESS(f"👌 Smart embedding stored for: {movie.title}"))