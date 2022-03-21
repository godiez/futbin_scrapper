import sys
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.core.mail import send_mail
from futbin.models import PlayerCardPrices, Percent
from datetime import datetime, timedelta


class Command(BaseCommand):
    @staticmethod
    def send_email(message):
        subject = 'Info WEB_EAPP'
        content_message = message
        email = settings.EMAIL_HOST_USER
        recipient_list = [settings.EMAIL_HOST_USER]
        send_mail(subject, content_message, email, recipient_list)

    @staticmethod
    def check_prices(data_by_player):
        try:
            obj = Percent.objects.get()
            percent = obj.percent
        except Percent.DoesNotExist as e:
            raise CommandError("Percentage isn't configured")
        result = {}
        for player_id, data in data_by_player.items():
            for ratio, dates_prices_by_card_type in data.get('values').items():
                for card_type, dates_prices in dates_prices_by_card_type.items():
                    if len(dates_prices) == 2:
                        old_price, new_price = dates_prices[:]
                        if old_price.get('price') == 0:
                            continue
                        to_past = old_price.get('price')
                        if to_past <= 0:
                            to_past = 1
                        increased_percent = ((new_price.get('price') - old_price.get('price')) / to_past) * 100
                        if increased_percent >= percent or increased_percent <= -percent:
                            if result.get(player_id):
                                result[player_id]['results'].append({
                                    'ratio': ratio,
                                    'card_type': card_type,
                                    'percent': increased_percent,
                                    'old_price': old_price.get('price'),
                                    'new_price': new_price.get('price'),
                                    'old_date': old_price.get('date'),
                                    'new_date': new_price.get('date'),
                                })
                            else:
                                result[player_id] = {'results': [], 'player_info': data.get('player_info')}
                                result[player_id]['results'] = [{
                                    'ratio': ratio,
                                    'card_type': card_type,
                                    'percent': increased_percent,
                                    'old_price': old_price.get('price'),
                                    'new_price': new_price.get('price'),
                                    'old_date': old_price.get('date'),
                                    'new_date': new_price.get('date'),
                                }]
        return result

    @staticmethod
    def player_info(card):
        return {'name': card.player.name, 'card_type': card.card.name}

    @staticmethod
    def format_data(data):
        html = ''
        cards = {'1': 'Gold Rare', '2': 'Gold IF', '3': 'UCL Non Rare'}
        for player_id, val in data.items():
            html += 'El jugador ' + val.get('player_info').get('name') + ' ha subido de precio en las siguientes cartas: \n'
            for values in val.get('results'):
                html += 'Tipo de carta: ' + cards.get(str(values.get('card_type'))) + ', Ratio: ' + str(values.get('ratio')) +', Precio antiguo: ' + \
                        str(values.get('old_price')) + ', Precio nuevo: ' + str(values.get('new_price')) + ', Porcentaje de crecimiento: ' + \
                        str(values.get('percent')) + '\n'
            html += '\n'
        return html

    def handle(self, *args, **options):
        # Notes
        # Date : Price must be 2 rows
        data_by_player = {}
        start = (datetime.today() - timedelta(hours=2))
        card_prices = PlayerCardPrices.objects.filter(date__gte=start)
        # Grouped data
        for card_price in card_prices.order_by('player_id', 'ratio', 'date'):
            _date = card_price.date.strftime('%Y-%m-%d %H:%M:%S')
            if data_by_player.get(card_price.player_id):
                if data_by_player[card_price.player_id]['values'].get(card_price.ratio):
                    if data_by_player[card_price.player_id]['values'][card_price.ratio].get(card_price.card_id):
                        data_by_player[card_price.player_id]['values'][card_price.ratio][card_price.card_id].append(
                            {'date': _date, 'price': card_price.price})
                    else:
                        data_by_player[card_price.player_id]['values'][card_price.ratio][card_price.card_id] = [{
                            'date': _date, 'price': card_price.price
                        }]
                else:
                    data_by_player[card_price.player_id]['values'][card_price.ratio] = {
                        card_price.card_id:
                            [{
                                'date': _date, 'price': card_price.price
                            }]
                    }
            else:
                data_by_player[card_price.player_id] = {'player_info': self.player_info(card_price), 'values': {}}
                data_by_player[card_price.player_id]['values'] = {
                    card_price.ratio:
                        {
                            card_price.card_id:
                                [{
                                    'date': _date, 'price': card_price.price
                                }]
                        }
                }
        increased_prices = self.check_prices(data_by_player)
        formatted_data = self.format_data(increased_prices)
        self.send_email(formatted_data)
