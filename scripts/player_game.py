"""
Use Pro Football Reference
"""
import re
import os
import urllib2
import datetime
from os import sys, path

import django
from bs4 import BeautifulSoup
from django.db.models import Q

sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "fantasy_nfl.settings")
django.setup()

from general.models import *

def sync(type_, val):
    # fit into roto
    val = val.strip().strip('@')
    conv = {
        'team': {
            'NOR': 'NO',
            'GNB': 'GB',
            'SFO': 'SF',
            'TAM': 'TB',
            'NWE': 'NE',
            'KAN': 'KC'
        },
        'name': {
        }
    }
    return conv[type_][val] if val in conv[type_] else val

def _C(val_dict, field):
    return float(val_dict.get(field, '0').strip() or '0')

def scrape(week):
    url = 'https://www.pro-football-reference.com/years/2019/week_{}.htm'.format(week)
    print "||" + url
    response = urllib2.urlopen(url)
    r = response.read()
    soup = BeautifulSoup(r, "html.parser")
    links = []
    for ii in soup.find_all("td", {"class": "right gamelink"}):
        if ii.find('a').text.strip() == 'Final':
            link = ii.find('a').get('href')
            links.append(link)

    for game_link in links:
        url = 'https://www.pro-football-reference.com' + game_link
        print "|| - " + url
        response = urllib2.urlopen(url)
        body = response.read()

        soup = BeautifulSoup(body, "html.parser")
        game_results = soup.find_all("div", {"class": "score"})
        home_score = int(game_results[0].text.strip())
        away_score = int(game_results[1].text.strip())

        # build the pos dict
        pos_dict = {}
        for table_id in ["home_snap_counts", "vis_snap_counts"]:
            tbl_text = body.split('<div class="overthrow table_container" id="div_{}">'.format(table_id))[1].split('</div>')[0]
            soup = BeautifulSoup(tbl_text, "html.parser")
            table = soup.find("table", {"id": table_id})
    
            for player in table.find("tbody").find_all("tr"):
                uid = player.find("th", {"data-stat": "player"}).get('data-append-csv')
                pos = player.find("td", {"data-stat": "pos"}).text.strip()
                pos_dict[uid] = pos

                if player.get('class'): # ignore header
                    break

        tbl_text = body.split('<div class="overthrow table_container" id="div_player_offense">')[1].split('</div>')[0]
        soup = BeautifulSoup(tbl_text, "html.parser")
        table = soup.find("table", {"id": "player_offense"})
        players = table.find("tbody").find_all("tr")

        home_team = sync('team', players[-1].find("td", {"data-stat": "team"}).text.strip())
        away_team = sync('team', players[0].find("td", {"data-stat": "team"}).text.strip())

        game_info = {
            home_team: [away_team, '', 'W' if home_score > away_score else 'T' if home_score == away_score else 'L'],
            away_team: [home_team, '@', 'L' if home_score > away_score else 'T' if home_score == away_score else 'W']
        }

        game_date = game_link[11:19]
        date = datetime.datetime.strptime(game_date, '%Y%m%d')

        # store team score
        defaults = {
            'name': home_team,
            'team': home_team,
            'opp': away_team,
            'pos': 'DEF',
            'game_location': '', 
            'fpts': home_score,
            'week_num': week,
            'date': date
        }

        PlayerGame.objects.update_or_create(name=home_team, date=date, defaults=defaults)

        defaults = {
            'name': away_team,
            'team': away_team,
            'opp': home_team,
            'pos': 'DEF',
            'game_location': '@', 
            'fpts': away_score,
            'week_num': week,
            'date': date
        }

        PlayerGame.objects.update_or_create(name=away_team, date=date, defaults=defaults)

        # build data for players
        for player in players:
            # try:
                if player.get('class'): # ignore header
                    continue

                name = player.find("th", {"data-stat": "player"}).text.strip()
                name = sync('name', name)
                uid = player.find("th", {"data-stat": "player"}).get('data-append-csv')

                defaults = {
                    'name': name,
                    'week_num': week
                }

                fields = ['team', 'pass_cmp', 'pass_att', 'pass_yds', 'pass_td', 'pass_int', 'pass_rating', 'pass_sacked', 
                          'pass_sacked_yds', 'pass_long', 'rush_att', 'rush_yds', 'rush_td', 'rush_long', 
                          'targets', 'rec', 'rec_yds', 'rec_td', 'rec_long', 'fumbles', 'fumbles_lost']

                for ii in fields:
                    field = player.find("td", {"data-stat": ii}).text.replace('%', '').strip()
                    if field:
                        defaults[ii] = field

                defaults['pos'] = pos_dict.get(uid, '')
                defaults['team'] = sync('team', defaults['team'])
                defaults['opp'] = game_info[defaults['team']][0]
                defaults['game_location'] = game_info[defaults['team']][1]
                defaults['game_result'] = game_info[defaults['team']][2]
                defaults['fpts'] = 0.1 * _C(defaults, 'rush_yds') + 6 * _C(defaults, 'rush_td') \
                                 + 0.04 * _C(defaults, 'pass_yds') + 4 * _C(defaults, 'pass_td') \
                                 - _C(defaults, 'pass_int') + 0.1 * _C(defaults, 'rec_yds') \
                                 + 6 * _C(defaults, 'rec_td') + 0.5 * _C(defaults, 'rec')

                PlayerGame.objects.update_or_create(uid=uid, date=date, defaults=defaults)
            # except Exception as e:
                # print(defaults)
                # print('------------------------------')
                # print(e)

if __name__ == "__main__":
    for week in range(1, 22):
        scrape(week)
