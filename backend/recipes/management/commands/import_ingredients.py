import csv

from django.core.management import BaseCommand

from recipes.models import Ingredient


class Command(BaseCommand):
    """Класс, реализующий загрузку информации в базу данных из файла."""
    def handle(self, *args, **options):
        with open('data/ingredients.csv', 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, fieldnames=['name', 'measurement_unit'])
            ingredients = [Ingredient(**row) for row in reader]
            Ingredient.objects.bulk_create(ingredients, ignore_conflicts=True)
            self.stdout.write('Успешно загружено!')
