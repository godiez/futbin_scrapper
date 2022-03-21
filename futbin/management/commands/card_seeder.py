import sys


from django.core.management.base import BaseCommand, CommandError
from futbin.models import Card
class Command(BaseCommand):

    def handle(self, *args, **options):
        Card.objects.all().delete()
        cards = [{'name': 'gold_rare'}, {'name': 'if_gold'},{'name': 'ucl_non_rare'}]
        for card in cards:
            Card.objects.create(**card)