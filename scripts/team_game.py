"""
Use Pro Football Reference for team stat
"""
import os
import datetime
from os import sys, path

import django
import requests
from bs4 import BeautifulSoup

sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "fantasy_nfl.settings")
django.setup()

from general.models import *
from general.views import current_season


# map roto -> pfr
team_map = {
    'NO': 'NOR',
    'GB': 'GNB',
    'SF': 'SFO',
    'TB': 'TAM',
    'NE': 'NWE',
    'KC': 'KAN',
    'HOU': 'HTX',
    'BAL': 'RAV',
    'LAR': 'RAM',
    'LAC': 'SDG',
    'TEN': 'OTI',
    'IND': 'CLT',
    'OAK': 'RAI',
    'ARI': 'CRD'
}

team_map_inv = {v: k for k, v in team_map.items()}

# create fields map for playergame
fields_map = { 'game_outcome': 'game_result', 'pass_yds_def': 'pass_sacked_yds',
               'pts_off': 'pass_cmp', 'pts_def': 'pass_att', 'first_down_off': 'pass_cmp_perc',
               'yards_off': 'pass_yds', 'pass_yds_off': 'pass_td', 'rush_yds_off': 'pass_int',
               'to_off': 'pass_rating', 'first_down_def': 'pass_sacked', 'yards_def': 'pass_long',
               'rush_yds_def': 'pass_yds_per_att', 'to_def': 'pass_adj_yds_per_att'
             }

def main(teams):
    year = current_season()

    for team in teams:
        _team = team.team
        __team = team_map.get(_team, _team)
        url = 'https://www.pro-football-reference.com/teams/{}/{}.htm'.format(__team.lower(), year)
        print(url)
        body = requests.get(url).text

        soup = BeautifulSoup(body, "html.parser")
        table = soup.find("table", {"id": "games"})
        team_infos = table.find("tbody").find_all("tr")

        for ti in team_infos:
            defaults = {
                'pos': 'DEF',
                'team': _team,
                'name': '{} {}'.format(team.first_name, team.last_name),
                'week_num': ti.find("th", {"data-stat": 'week_num'}).text.strip(),
                'game_location': ti.find("td", {"data-stat": 'game_location'}).text.strip()
            }

            for _field, mfield in fields_map.items():
                defaults[mfield] = ti.find("td", {"data-stat": _field}).text.strip() or 0

            if not defaults['game_result']:
                continue

            game_date = ti.find("td", {"data-stat": 'game_date'}).get('csk')
            opp = ti.find("td", {"data-stat": 'opp'}).find('a').get('href')[7:10].upper()
            
            defaults['date'] = datetime.datetime.strptime(game_date, '%Y-%m-%d')
            defaults['opp'] = team_map_inv.get(opp, opp)

            PlayerGame.objects.update_or_create(name=defaults['name'], date=defaults['date'], defaults=defaults)


if __name__ == "__main__":
    teams = Player.objects.filter(data_source='FanDuel', position='DEF')
    main(teams)
