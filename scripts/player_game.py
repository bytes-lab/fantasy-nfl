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
    # bball -> roto
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

def scrape(param):
    dp = "https://www.pro-football-reference.com/play-index/pgl_finder.cgi?request=1&match=game&year_min=2018&year_max=2018&season_start=1&season_end=-1&age_min=0&age_max=99&game_type=A&league_id=&team_id=&opp_id=&game_num_min=0&game_num_max=99&game_location=&game_result=&handedness=&is_active=&is_hof=&from_link=1&" + param
    print (dp)
    response = urllib2.urlopen(dp)
    r = response.read()

    soup = BeautifulSoup(r, "html.parser")

    try:
        table = soup.find("table", {"id":"results"})
        player_rows = table.find("tbody")
        players = player_rows.find_all("tr")
    except Exception as e:
        print (e)
        return  # no players

    for player in players:
        try:
            if player.get('class'): # ignore header
                continue

            name = player.find("td", {"data-stat":"player"}).text.strip()
            name = sync('name', name)
            pos = player.find("td", {"data-stat":"pos"}).text
            game_date = player.find("td", {"data-stat":"game_date"}).text
            team = player.find("td", {"data-stat":"team"}).text.strip()
            team = sync('team', team)
            opp = player.find("td", {"data-stat":"opp"}).text
            opp = sync('team', opp)

            pid = player.find("td", {"data-stat":"player"}).get('data-append-csv')
            player_ = Player.objects.filter(first_name__iexact=name.split(' ')[0],
                                            last_name__iexact=name.split(' ')[1],
                                            team=team)
            # update avatar for possible new players
            avatar = 'https://d395i9ljze9h3x.cloudfront.net/req/20180910/images/headshots/{}_2018.jpg'.format(pid)
            player_.update(avatar=avatar)

            defaults = {
                'location': player.find("td", {"data-stat":"game_location"}).text,
                'opp': opp,
                'game_result': player.find("td", {"data-stat":"game_result"}).text,
                'targets': int(player.find("td", {"data-stat":"targets"}).text),
                'rec': player.find("td", {"data-stat":"rec"}).text,
                'rec_yds': player.find("td", {"data-stat":"rec_yds"}).text or None,
                'rec_yds_per_rec': player.find("td", {"data-stat":"rec_yds_per_rec"}).text,
                'rec_td': int(player.find("td", {"data-stat":"rec_td"}).text),
                'catch_pct': player.find("td", {"data-stat":"catch_pct"}).text or None,
                'rec_yds_per_tgt': player.find("td", {"data-stat":"rec_yds_per_tgt"}).text,
                'name': name,
                'pos': pos,
                'game_date': game_date,
                'team': team
            }

            # PlayerGame.objects.update_or_create(name=name, team=team, date=date, defaults=defaults)
            print defaults
        except (Exception) as e:
            print (e)
    

if __name__ == "__main__":
    # take care of pagination, week, type
    param = "week_num_min=3&week_num_max=5&game_day_of_week=&c1stat=rec&c1comp=gt&c1val=1&c2stat=&c2comp=gt&c2val=&c3stat=&c3comp=gt&c3val=&c4stat=&c4comp=gt&c4val=&order_by=rec_yds"
    # for delta in range(3):
    #     date = datetime.datetime.now() + datetime.timedelta(days=-delta)
    #     param = 'month={}&day={}&year={}&type=all'.format(date.month, date.day, date.year)
    scrape(param)
