"""
Use Pro Football Reference
"""
import urllib2

from bs4 import BeautifulSoup

import os
from os import sys, path
import django
import pdb

import datetime

sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "fantasy_nfl.settings")
django.setup()

from general.models import *

def sync(type_, val):
    # fit into roto
    val = val.strip().strip('@')
    conv = {
        'team': {
            'GSW': 'GS',
            'CHO': 'CHA',
            'NOP': 'NO',
            'SAS': 'SA',
            'BRK': 'BKN',
            'NYK': 'NY'
        },
        'name': {
            'Juan Hernangomez': 'Juancho Hernangomez',
            'CJ McCollum': 'C.J. McCollum',
            'Taurean Waller-Prince': 'Taurean Prince',
        }
    }
    return conv[type_][val] if val in conv[type_] else val

def _C(val):
    return int(val) if val else 0

def scrape(week):
    url = "https://www.pro-football-reference.com/play-index/pgl_finder.cgi?request=1&match=game&year_min=2018&year_max=2018&season_start=1&season_end=-1&age_min=0&age_max=99&game_type=A&league_id=&team_id=&opp_id=&game_num_min=0&game_num_max=99&game_location=&game_result=&handedness=&is_active=&is_hof=&from_link=1&"

    for type_ in ['pass_att', 'rush_att', 'rec']:
        param = "week_num_min={0}&week_num_max={0}&game_day_of_week=&c1stat={1}&c1comp=gt&c1val=1&c2stat=&c2comp=gt&c2val=&c3stat=&c3comp=gt&c3val=&c4stat=&c4comp=gt&c4val=&order_by=age".format(week, type_)
        offset = 0
        while True:
            _offset = '&offset={}'.format(offset)
            dp = url + param + _offset
            print (dp)

            try:
                response = urllib2.urlopen(dp)
                r = response.read()
                soup = BeautifulSoup(r, "html.parser")
                table = soup.find("table", {"id":"results"})
                player_rows = table.find("tbody")
                players = player_rows.find_all("tr")
                if not players:
                    break
            except Exception as e:
                print('***', e, '***')
                break  # no players

            for player in players:
                try:
                    if player.get('class'): # ignore header
                        continue

                    name = player.find("td", {"data-stat":"player"}).text.strip()
                    name = sync('name', name)
                    game_date = player.find("td", {"data-stat":"game_date"}).text            
                    date = datetime.datetime.strptime(game_date, '%Y-%m-%d')
                    uid = player.find("td", {"data-stat":"player"}).get('data-append-csv')

                    defaults = {
                        'name': name,
                        'week_num': week
                    }

                    fields = ['team', 'game_location', 'opp', 'game_result', 'pos', 'pass_cmp', 'pass_att', 'pass_cmp_perc', 
                              'pass_yds', 'pass_td', 'pass_td', 'pass_int', 'pass_rating', 'pass_sacked', 'pass_sacked_yds', 
                              'pass_yds_per_att', 'pass_adj_yds_per_att', 'rush_att', 'rush_yds', 'rush_yds_per_att', 'rush_td', 
                              'targets', 'rec', 'rec_yds', 'rec_yds_per_rec', 'rec_td', 'catch_pct', 'rec_yds_per_tgt', 'all_td', 
                              'fumbles', 'fumbles_forced', 'fumbles_rec', 'fumbles_rec_yds', 'fumbles_rec_td']

                    for ii in fields:
                        field = player.find("td", {"data-stat": ii})
                        defaults[ii] = field.text.replace('%', '') if field else None

                    defaults['team'] = sync('team', defaults['team'])
                    defaults['opp'] = sync('team', defaults['opp'])
                    defaults['fpts'] = 0.1 * _C(defaults['rush_yds']) + 6 * _C(defaults['rush_td']) 
                                     + 0.04 * _C(defaults['pass_yds']) + 4 * _C(defaults['pass_td'])
                                     - _C(defaults['pass_int']) + 0.1 * _C(defaults['rec_yds'])
                                     + 6 * _C(defaults['rec_td']) + 0.5 * _C(defaults['rec'])

                    player_ = Player.objects.filter(first_name__iexact=name.split(' ')[0],
                                                    last_name__iexact=name.split(' ')[1],
                                                    team=defaults['team'])
                    # update avatar for possible new players
                    avatar = 'https://d395i9ljze9h3x.cloudfront.net/req/20180910/images/headshots/{}_2018.jpg'.format(uid)
                    player_.update(avatar=avatar)

                    PlayerGame.objects.update_or_create(uid=uid, date=date, defaults=defaults)
                except (Exception) as e:
                    print defaults
                    print (e)
            offset += 100
    

if __name__ == "__main__":
    for week in range(9, 12):
        scrape(week)
