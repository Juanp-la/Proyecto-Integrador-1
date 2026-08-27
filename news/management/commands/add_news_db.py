import csv
import os
from datetime import datetime
from django.core.management.base import BaseCommand
from news.models import News

NEWS_TO_IMPORT = 5

class Command(BaseCommand):
    help = 'Loads news from Fake.csv into the News model'

    def handle(self, *args, **options):
        csv_path = os.path.join(os.path.dirname(__file__), 'Fake.csv')

        count = 0
        with open(csv_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                if count >= NEWS_TO_IMPORT:
                    break

                headline = row.get('title', '').strip()
                body = row.get('text', '').strip()
                date_str = row.get('date', '').strip()

                if not headline or not date_str:
                    continue

                try:
                    date_value = datetime.strptime(date_str, '%B %d, %Y').date()
                except ValueError:
                    continue  # se salta filas con fecha en formato raro

                News.objects.create(
                    headline=headline,
                    body=body,
                    date=date_value,
                )
                count += 1

        self.stdout.write(self.style.SUCCESS(f'Imported {count} news items from Fake.csv'))