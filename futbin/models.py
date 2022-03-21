from django.db import models

# Create your models here.


class Player(models.Model):
    id = models.PositiveIntegerField(primary_key=True)
    name = models.CharField(max_length=200)
    cards = models.ManyToManyField('Card', through='PlayerCardPrices')

    def __str__(self):
        return self.name


class Card(models.Model):
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name


class PlayerCardPrices(models.Model):
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    card = models.ForeignKey(Card, on_delete=models.CASCADE)
    price = models.FloatField()
    ratio = models.PositiveSmallIntegerField(null=False)
    date = models.DateTimeField()

    def __str__(self):
        return self.player.name

class Percent(models.Model):
    percent = models.PositiveIntegerField()

    def __str__(self):
        return str(self.percent)
