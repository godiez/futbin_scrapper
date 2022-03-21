import sys

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand, CommandError
from bs4 import BeautifulSoup
import requests as rq
from django.core.mail import send_mail
from futbin.models import Card
from futbin.models import Player
from futbin.models import PlayerCardPrices
import datetime
import time


class Command(BaseCommand):
    LIMIT_PETITIONS = 50
    @staticmethod
    def send_email(self, message):
        subject = 'Info WEB_EAPP'
        message = message
        email = settings.EMAIL_HOST_USER
        recipient_list = [settings.EMAIL_HOST_USER]
        send_mail(subject, message, email, recipient_list)

    @staticmethod
    def clean_price(price, lyric):
        final_price = 0.0
        max_digits_M = 6
        max_digits_K = 3
        if isinstance(price, str):
            if price is not '':
                all_price = price.split('.')
                if lyric is not '':
                    len_decimals = to_add = 0
                    to_show = ''
                    if len(all_price) == 2:
                        len_decimals = len(all_price[1])
                        to_show = all_price[1]
                    if lyric is 'K':
                        to_add = max_digits_K - len_decimals
                    elif lyric is 'M':
                        to_add = max_digits_M - len_decimals
                    final_price = int(all_price[0] + str(to_show)) * (10 ** to_add)
                else:
                    final_price = int(all_price[0])
        return final_price

    @staticmethod
    def get_unique_id(href):
        id = ''
        split = href.split('/')
        if len(split) >= 4:
            id = split[3]
        return int(id)

    @staticmethod
    def get_player_id(content_player):
        id = 0
        page_info = content_player.find(id="page-info")
        if page_info:
            id = page_info['data-baseid']
        return int(id)

    @staticmethod
    def get_player_name(content_player):
        name = ''
        split = content_player.split('/')
        if len(split) >= 4:
            name = split[-1].strip()
        return name

    @staticmethod
    def get_player_ratio(content_player):
        ratio = 0
        if len(content_player) >= 1:
            result = content_player[0]
            ratio = int(result.getText())
        return ratio

    def handle(self, *args, **options):
        start = time.time()
        #https://www.futbin.com/players?page=2&version=gold_rare
        base_url = 'https://www.futbin.com'
        current_year = '21'
        players_endpoint = 'players'
        single_player_endpoint = 'player'
        response = []
        card_filters = Card.objects.all()
        current_page = 1
        players_already = {}
        amount_petitions = 0
        for filter in card_filters:
            current_page = limit_page = 1
            while current_page <= limit_page:
                if amount_petitions > self.LIMIT_PETITIONS:
                    time.sleep(120)
                    amount_petitions = 0
                try:
                    response = rq.get(base_url + '/' + players_endpoint + '?page=' + str(current_page) + '&version=' + filter.name)
                    amount_petitions = amount_petitions + 1
                except rq.exceptions.RequestException as e:
                    print(e)
                if response.status_code == 200:
                    content = BeautifulSoup(response.text, 'html.parser')
                    table = content.find(id="repTb")
                    pagination = content.find_all('ul', class_="pagination")
                    elem = None
                    for lis in pagination:
                        elem = lis.find_all('li')
                    if elem:
                        limit_page = int(elem[-2].getText().strip())
                    #player_already = response_player = None
                    #player_already = None
                    for tr in table.findAll('tr'):
                        response_player = player_already =  None
                        tr_data = tr.find_all("a", class_="player_name_players_table")[0]
                        id = self.get_unique_id(tr_data.attrs['href'])
                        player_name = self.get_player_name(tr_data.attrs['href'])
                        ratio = self.get_player_ratio(tr.find_all("span", class_="rating"))
                        real_player_id = 0
                        try:
                            player_already = Player.objects.get(name=player_name)
                        except Player.DoesNotExist as e:
                            #TODO: Audit log
                            pass
                        if not player_already:
                            if amount_petitions > self.LIMIT_PETITIONS:
                                time.sleep(120)
                                amount_petitions = 0
                            try:
                                response_player = rq.get(base_url + '/' + current_year + '/' + single_player_endpoint + '/' + str(id))
                                amount_petitions = amount_petitions + 1
                            except rq.exceptions.RequestException as e:
                                #TODO: Audit log
                                pass
                        else:
                            real_player_id = player_already.id
                        if response_player and response_player.status_code == 200:
                            content_player = BeautifulSoup(response_player.text, 'html.parser')
                            real_player_id = self.get_player_id(content_player)

                        tr_price = tr.find_all("span", class_="ps4_color")[0].getText().strip()
                        price = tr_price
                        lyric = ''
                        if 'K' in tr_price or 'M' in tr_price:
                            price = tr_price[:-1]
                            lyric = tr_price[-1]

                        price = self.clean_price(price, lyric)
                        playerObj, created = Player.objects.update_or_create(
                            id=real_player_id,
                            defaults={"name": player_name}
                        )
                        if playerObj:
                            pricesObj, created = PlayerCardPrices.objects.update_or_create(
                                player=playerObj,
                                card=filter,
                                ratio=ratio,
                                date=datetime.datetime.now().strftime("%Y-%m-%d %H:00"),
                                defaults={"price": price}
                            )
                current_page = current_page + 1
        print((time.time() - start), "seconds")
