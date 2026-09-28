import os
from huggingface_hub import InferenceClient
from dotenv import load_dotenv
from django.core.management.base import BaseCommand
from movie.models import Movie

class Command(BaseCommand):
    help = "Genera una imagen con IA (Hugging Face) para la primera película y actualiza la base de datos"

    def generate_and_download_image(self, client, movie_title, save_folder):
        prompt = f"Movie poster of {movie_title}"
        image = client.text_to_image(
            prompt,
            model="stabilityai/stable-diffusion-3-medium-diffusers",
        )

        image_filename = f"m_{movie_title}.png"
        image_path_full = os.path.join(save_folder, image_filename)
        image.save(image_path_full)

        return os.path.join('movie/images', image_filename)

    def handle(self, *args, **kwargs):
        load_dotenv('huggingface.env')
        client = InferenceClient(
            provider="hf-inference",
            api_key=os.environ.get('hf_token'),
        )

        images_folder = 'media/movie/images/'
        os.makedirs(images_folder, exist_ok=True)

        movies = Movie.objects.all()
        self.stdout.write(f"Found {movies.count()} movies")

        for movie in movies:
            image_relative_path = self.generate_and_download_image(client, movie.title, images_folder)
            movie.image = image_relative_path
            movie.save()
            self.stdout.write(self.style.SUCCESS(f"Saved and updated image for: {movie.title}"))
            break