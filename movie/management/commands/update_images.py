import os
import requests
from urllib.parse import quote
from django.core.management.base import BaseCommand
from django.conf import settings
from movie.models import Movie

class Command(BaseCommand):
    help = 'Update movie images using an alternative free API (Pollinations AI)'

    def generate_and_download_image(self, movie_title, save_folder):
        # Codificamos el título para que sea seguro en una URL
        prompt = quote(f"Movie poster of {movie_title}, high quality, cinematic")
        
        # Llamamos a la API gratuita de Pollinations
        image_url = f"https://image.pollinations.ai/prompt/{prompt}?width=512&height=512&nologo=true"

        image_filename = f"m_{movie_title.replace(' ', '_')}.png"
        image_path_full = os.path.join(save_folder, image_filename)

        image_response = requests.get(image_url)
        image_response.raise_for_status()
        with open(image_path_full, 'wb') as f:
            f.write(image_response.content)

        return os.path.join('movie/images', image_filename)

    def handle(self, *args, **kwargs):
        images_folder = 'media/movie/images/'
        os.makedirs(images_folder, exist_ok=True)

        movies = Movie.objects.all()
        self.stdout.write(f"Found {movies.count()} movies")

        for movie in movies:
            try:
                self.stdout.write(f"Generando imagen para: {movie.title} con API externa...")
                image_relative_path = self.generate_and_download_image(movie.title, images_folder)
                movie.image = image_relative_path
                movie.save()
                self.stdout.write(self.style.SUCCESS(f"Saved and updated image for: {movie.title}"))
            except Exception as e:
                self.stderr.write(self.style.ERROR(f"Error con {movie.title}: {e}"))