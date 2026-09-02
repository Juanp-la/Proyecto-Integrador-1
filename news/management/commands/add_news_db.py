import csv
import os
from datetime import datetime
from django.core.management.base import BaseCommand
from news.models import News

class Command(BaseCommand):
    help = 'Carga 5 noticias desde Fake.csv a la base de datos'

    def handle(self, *args, **kwargs):
        csv_path = os.path.join(os.path.dirname(__file__), 'Fake.csv')

        count = 0
        with open(csv_path, encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                if count >= 5:
                    break

                headline = row.get('title', '').strip()
                body = row.get('text', '').strip()
                date_str = row.get('date', '').strip()

                if not headline or not date_str:
                    continue

                try:
                    date_value = datetime.strptime(date_str, '%B %d, %Y').date()
                except ValueError:
                    continue

                news_item = News(
                    headline=headline[:200],
                    body=body,
                    date=date_value
                )
                news_item.save()
                count += 1

        self.stdout.write(self.style.SUCCESS(f'Se cargaron {count} noticias exitosamente'))