import os
import numpy as np
from django.core.management.base import BaseCommand
from movie.models import Movie

class Command(BaseCommand):
    help = 'Calculate movie similarities using local mock embeddings to bypass network errors'

    def handle(self, *args, **kwargs):
        
        def get_embedding(text):
            # MOCK: Simula una API de IA generando un vector matemático a partir del texto
            # Usamos una semilla basada en el texto para que siempre dé el mismo resultado para la misma película
            np.random.seed(sum(ord(c) for c in text))
            return np.random.rand(1536).astype(np.float32)

        def cosine_similarity(a, b):
            return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

        try:
            movie1 = Movie.objects.get(title="Spider-Man")
            movie2 = Movie.objects.get(title="The Dark Knight")

            self.stdout.write("Generando embeddings para las películas (Mock Local)...")
            emb1 = get_embedding(movie1.description)
            emb2 = get_embedding(movie2.description)

            # Similitud entre las dos películas
            similarity = cosine_similarity(emb1, emb2)
            self.stdout.write(self.style.SUCCESS(f"🎬 '{movie1.title}' vs '{movie2.title}': {similarity:.4f}"))

            # Búsqueda contra un texto libre (Prompt)
            prompt = "película oscura sobre un héroe enmascarado luchando contra el crimen"
            self.stdout.write(f"Generando embedding para el prompt: '{prompt}'...")
            prompt_emb = get_embedding(prompt)

            sim_prompt_movie1 = cosine_similarity(prompt_emb, emb1)
            sim_prompt_movie2 = cosine_similarity(prompt_emb, emb2)

            self.stdout.write(self.style.SUCCESS(f"📝 Similitud prompt vs '{movie1.title}': {sim_prompt_movie1:.4f}"))
            self.stdout.write(self.style.SUCCESS(f"📝 Similitud prompt vs '{movie2.title}': {sim_prompt_movie2:.4f}"))

        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Error: {e}"))