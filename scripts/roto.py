import os
import requests

from os import sys, path

import django

sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "fantasy_nfl.settings")
django.setup()

from general.models import *
from general.constants import DATA_SOURCE
from general import html2text
from scripts.get_slate import get_slate


def get_players(data_source, data_source_id, teams):
    fields = ['opponent', 'proj_points', 'salary', 'team']

    try:
        slate_id = get_slate(data_source)
        url = 'https://www.rotowire.com/daily/tables/optimizer-nfl.php' + \
              '?siteID={}&slateID={}&projSource=RotoWire&oshipSource=RotoWire'.format(data_source_id, slate_id)
        print(url)

        players = requests.get(url).json()
        print('Number of players:', len(players))
        if len(players) > 10:
            print(data_source, len(players))
            for ii in players:
                defaults = { key: str(ii[key]).replace(',', '') for key in fields }
                defaults['position'] = ii['position'] if ii['position'] != 'D' else 'DEF'
                defaults['available'] = ii['team'] in teams
                defaults['injury'] = html2text.html2text(ii['injury']).strip().upper()
                defaults['first_name'] = ii['first_name'].replace('.', '')
                defaults['last_name'] = ii['last_name'].replace('.', '')
                defaults['value'] = ii['salary'] / 250.0 + 10

                Player.objects.update_or_create(uid=ii['id'], data_source=data_source, defaults=defaults)
    except:
        print('*** Something is wrong ***')


if __name__ == "__main__":
    games = Game.objects.all()
    teams = [ii.home_team for ii in games] + [ii.visit_team for ii in games]
    Player.objects.all().update(available=False)

    for id, ds in enumerate(DATA_SOURCE, 1):
        get_players(ds[0], id, teams)
