import requests
import os
from os import sys, path
import django

sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "fantasy_nfl.settings")
django.setup()

from general.models import *
from general import html2text

def get_players(data_source, teams):
    fields = ['first_name', 'last_name', 'money_line', 
              'point_spread', 'position', 'proj_ceiling', 'opponent',
              'proj_custom', 'proj_floor', 'proj_original', 'proj_points', 'proj_rotowire', 
              'proj_third_party_one', 'proj_third_party_two', 'actual_position', 
              'salary', 'team', 'team_points']

    try:
        slates = ['Thu-Mon', 'Sat-Mon'] if data_source in ['FanDuel', 'DraftKings'] else ['all']
        for slate in slates:
            url = 'https://www.rotowire.com/daily/tables/optimizer-nfl.php?sport=NFL&' + \
                  'site={}&projections=&type=main&slate={}'.format(data_source, slate)
            players = requests.get(url).json()
            if len(players) > 100:
                print data_source, len(players)
                for ii in players:
                    defaults = { key: str(ii[key]).replace(',', '') for key in fields }
                    defaults['available'] = ii['team'] in teams
                    defaults['injury'] = html2text.html2text(ii['injury']).strip().upper()
                    Player.objects.update_or_create(uid=ii['id'], data_source=data_source, defaults=defaults)
                break
    except:
        print('*** Something is wrong ***')


if __name__ == "__main__":
    games = Game.objects.all()
    teams = [ii.home_team for ii in games] + [ii.visit_team for ii in games]
    Player.objects.all().update(available=False)

    for ds in DATA_SOURCE:
        get_players(ds[0], teams)
