import requests
import os
from os import sys, path
import django

sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "fantasy_nfl.settings")
django.setup()

from general.models import *
from general import html2text

def sync(type_, val):
    # fit into roto
    val = val.strip().strip('@')
    conv = {
        'team': {
            "WAS": "WSH"
        },
        'name': {
            "Gurley II": "Gurley",
            "Webb III": "Webb",
            "Fuller V": "Fuller",
        }
    }
    return conv[type_][val] if val in conv[type_] else val


def get_avatars(teams):
    Player.objects.all().update(eid=-1)

    for team in teams:
        # try:
            url = 'http://site.web.api.espn.com/apis/site/v2/sports/football/nfl/teams/{}/roster'.format(sync("team", team).lower())
            print "======================", url
            players = requests.get(url).json()['athletes']
            _players = players[0]['items'] + players[1]['items'] + players[2]['items']

            for ii in _players:
                first_name = sync("name", ii['firstName']).replace('.', '')
                last_name = sync("name", ii['lastName']).replace('.', '')
                Player.objects.filter(team=team, first_name=first_name, last_name=last_name).update(eid=ii['id'])
        # except:
        #     print('*** Something is wrong ***')


if __name__ == "__main__":
    teams = Player.objects.all().values_list('team', flat=True).distinct()
    get_avatars(teams)
