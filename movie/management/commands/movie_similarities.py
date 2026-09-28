import os
import numpy as np
from huggingface_hub import InferenceClient
from dotenv import load_dotenv
from django.core.management.base import BaseCommand
from movie.models import Movie

class Command(BaseCommand):
    help = "Calcula la similitud de coseno entre dos películas y un prompt usando embeddings de Hugging Face"

    def get_embedding(self, client, text):
        result = client.feature_extraction(
            text,
            model="sentence-transformers/all-MiniLM-L6-v2",
        )
        return np.array(result, dtype=np.float32).flatten()

    def cosine_similarity(self, a, b):
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

    def handle(self, *args, **kwargs):
        load_dotenv('huggingface.env')
        client = InferenceClient(
            provider="hf-inference",
            api_key=os.environ.get('hf_token'),
        )

        movie1 = Movie.objects.get(title="spiderman")
        movie2 = Movie.objects.get(title="batman")

        emb1 = self.get_embedding(client, movie1.description)
        emb2 = self.get_embedding(client, movie2.description)

        similarity = self.cosine_similarity(emb1, emb2)
        self.stdout.write(f"🎬 {movie1.title} vs {movie2.title}: {similarity:.4f}")

        prompt = "película de superhéroes con acción y villanos"
        prompt_emb = self.get_embedding(client, prompt)

        sim_prompt_movie1 = self.cosine_similarity(prompt_emb, emb1)
        sim_prompt_movie2 = self.cosine_similarity(prompt_emb, emb2)

        self.stdout.write(f"📝 Similitud prompt vs '{movie1.title}': {sim_prompt_movie1:.4f}")
        self.stdout.write(f"📝 Similitud prompt vs '{movie2.title}': {sim_prompt_movie2:.4f}")