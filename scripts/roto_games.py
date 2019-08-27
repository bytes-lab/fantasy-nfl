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

def get_games():
    # try:
        site = 'FanDuel'
        slate, type = get_slate(site)
        url = 'https://www.rotowire.com/daily/tables/schedule.php?sport=NFL&site={}&type={}&slate={}'.format(site, type, slate)

        games = requests.get(url).json()
        if games:
            Game.objects.all().delete()
            fields = ['game_status', 'ml', 'home_team', 'visit_team', 'date']
            for ii in games:
                if ii['game_status'] == 'upcoming':
                    defaults = { key: ii[key] for key in fields }
                    defaults['ou'] = float(ii.get('ou', 0))
                    Game.objects.create(**defaults)
            # build_TMS_cache()
            # build_player_cache()
    # except:
    #     pass

if __name__ == "__main__":
    get_games()
