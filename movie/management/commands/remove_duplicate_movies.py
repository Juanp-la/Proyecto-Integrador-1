from django.core.management.base import BaseCommand
from movie.models import Movie
from django.db.models import Count

class Command(BaseCommand):
    help = "Elimina películas duplicadas por título, conservando la más antigua"

    def handle(self, *args, **kwargs):
        duplicates = (
            Movie.objects.values('title')
            .annotate(title_count=Count('id'))
            .filter(title_count__gt=1)
        )

        total_deleted = 0
        for entry in duplicates:
            title = entry['title']
            movies = Movie.objects.filter(title=title).order_by('id')
            keep = movies.first()
            to_delete = movies.exclude(id=keep.id)
            count = to_delete.count()
            to_delete.delete()
            total_deleted += count
            self.stdout.write(f"'{title}': eliminadas {count} duplicada(s), se conservó id {keep.id}")

        self.stdout.write(self.style.SUCCESS(f"Total de duplicados eliminados: {total_deleted}"))