import requests

import os
from os import sys, path
import django

sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "fantasy_nfl.settings")
django.setup()

from general.models import *
from general.views import *
from scripts.get_slate import get_slate

def get_games(data_source, data_source_id):
    # try:
        slate_id = get_slate(data_source)
        url = 'https://www.rotowire.com/daily/tables/nfl/schedule.php' + \
            '?siteID={}&slateID={}'.format(data_source_id, slate_id)

        games = requests.get(url).json()
        if games:
            Game.objects.all().delete()
            fields = ['ml', 'home_team', 'visit_team', 'date']
            for ii in games:
                defaults = { key: ii[key] for key in fields }
                defaults['ou'] = float(ii['ou'] or 0)
                Game.objects.create(**defaults)
            build_TMS_cache()
            build_player_cache()
    # except:
    #     pass

if __name__ == "__main__":
    get_games('FanDuel', 2)
