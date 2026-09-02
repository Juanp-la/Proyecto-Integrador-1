import os
import pandas as pd
from datetime import datetime
from django.core.management.base import BaseCommand
from news.models import News


class Command(BaseCommand):
    help = 'Puebla la base de datos de noticias a partir de Fake.csv (dataset de Kaggle)'

    def handle(self, *args, **options):
        # Ruta esperada del CSV: dentro de esta misma carpeta (news/management/commands/)
        csv_path = os.path.join(os.path.dirname(__file__), 'Fake.csv')

        if not os.path.exists(csv_path):
            self.stdout.write(self.style.ERROR(
                f'No se encontro el archivo: {csv_path}\n'
                'Descarga Fake.csv desde Kaggle y colocalo en news/management/commands/'
            ))
            return

        df = pd.read_csv(csv_path)

        def find_col(possible_names):
            for col in df.columns:
                if col.strip().lower() in possible_names:
                    return col
            return None

        title_col = find_col(['title', 'headline'])
        text_col = find_col(['text', 'body', 'content'])
        date_col = find_col(['date'])

        if not title_col or not date_col:
            self.stdout.write(self.style.ERROR(
                f'Columnas esperadas no encontradas. Columnas disponibles: {list(df.columns)}'
            ))
            return

        # Solo 5 noticias, como pide el taller
        df = df.head(5)

        created_count = 0
        for _, row in df.iterrows():
            headline = str(row[title_col]).strip()[:200]
            body = str(row[text_col]).strip() if text_col and pd.notna(row[text_col]) else ''

            date_value = None
            try:
                date_value = datetime.strptime(str(row[date_col]).strip(), '%B %d, %Y').date()
            except ValueError:
                # Si el formato de fecha del CSV es distinto, se deja la fecha de hoy
                date_value = datetime.today().date()

            News.objects.create(
                headline=headline,
                body=body,
                date=date_value,
            )
            created_count += 1

        self.stdout.write(self.style.SUCCESS(
            f'{created_count} noticias agregadas a la base de datos.'
        ))
