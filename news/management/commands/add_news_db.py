import csv
import datetime

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand

from news.models import News

CSV_NAME = 'Fake.csv'
NUM_NEWS = 5
# Imágenes estáticas ya existentes en el proyecto (una por cada noticia).
IMAGES = ['news1.png', 'news2.png', 'news3.png', 'news4.png', 'news5.png']


class Command(BaseCommand):
    help = 'Puebla la tabla News a partir de Fake.csv (title, text, subject, date).'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Borra las noticias existentes antes de cargar las nuevas.',
        )

    def handle(self, *args, **options):
        csv_path = settings.BASE_DIR / CSV_NAME
        if not csv_path.exists():
            self.stderr.write(self.style.ERROR(
                f'No se encontró {CSV_NAME} en {settings.BASE_DIR}. '
                'Copia el archivo ahí antes de ejecutar este comando.'
            ))
            return

        if options['reset']:
            deleted, _ = News.objects.all().delete()
            self.stdout.write(f'Se eliminaron {deleted} noticias existentes.')

        static_dir = settings.BASE_DIR / 'news' / 'static' / 'news' / 'img'

        created = 0
        with open(csv_path, encoding='utf-8', errors='replace') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if created >= NUM_NEWS:
                    break

                title = (row.get('title') or '').strip()
                text = (row.get('text') or '').strip()
                date_raw = (row.get('date') or '').strip()

                if not (title and text and date_raw):
                    continue

                # Fake.csv trae fechas como "December 31, 2017". Algunas filas
                # traen basura (URLs, etc.) en la columna date; esas se saltan.
                try:
                    date_value = datetime.datetime.strptime(
                        date_raw, '%B %d, %Y'
                    ).date()
                except ValueError:
                    continue

                if News.objects.filter(title=title).exists():
                    continue

                image_file = IMAGES[created % len(IMAGES)]
                image_path = static_dir / image_file
                if not image_path.exists():
                    self.stderr.write(self.style.WARNING(
                        f'No se encontró {image_path}, se omite "{title}".'
                    ))
                    continue

                with open(image_path, 'rb') as img_f:
                    image_data = img_f.read()

                news_item = News(
                    title=title[:150],
                    summary=text[:300],
                    published_at=date_value,
                )
                news_item.image.save(image_file, ContentFile(image_data), save=False)
                news_item.save()

                created += 1
                self.stdout.write(f'  Creada noticia: {title} ({date_value})')

        self.stdout.write(self.style.SUCCESS(
            f'Listo. Se crearon {created} noticias nuevas a partir de {CSV_NAME}.'
        ))
