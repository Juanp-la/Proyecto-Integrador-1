import os
import time
import numpy as np
from huggingface_hub import InferenceClient
from dotenv import load_dotenv
from django.core.management.base import BaseCommand
from movie.models import Movie

class Command(BaseCommand):
    help = "Genera y almacena embeddings para todas las películas usando Hugging Face"

    def handle(self, *args, **kwargs):
        load_dotenv('huggingface.env')
        client = InferenceClient(
            provider="hf-inference",
            api_key=os.environ.get('hf_token'),
        )

        movies = Movie.objects.all()
        self.stdout.write(f"Found {movies.count()} movies in the database")

        for movie in movies:
            try:
                result = client.feature_extraction(
                    movie.description,
                    model="sentence-transformers/all-MiniLM-L6-v2",
                )
                result_arr = np.array(result, dtype=np.float32)
                if result_arr.ndim == 2:
                    result_arr = result_arr.mean(axis=0)
                embedding = result_arr.flatten()
                movie.emb = embedding.tobytes()
                movie.save()
                self.stdout.write(self.style.SUCCESS(f"👌 Embedding stored for: {movie.title}"))
                time.sleep(0.5)
            except Exception as e:
                self.stderr.write(f"Failed for {movie.title}: {str(e)}")
                time.sleep(2)

        self.stdout.write(self.style.SUCCESS("🌟 Finished generating embeddings for all movies"))