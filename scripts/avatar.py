import os
import requests
from os import sys, path

import django
from PIL import Image

sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "fantasy_nfl.settings")
django.setup()

from django.conf import settings

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

                eid = ii['id']
                img_path = path.join(settings.BASE_DIR, "static/media")
                normal_file = img_path + "/normal/{}.png".format(eid)
                icon_file = img_path + "/icon/{}.png".format(eid)
                img_url = 'http://a.espncdn.com/combiner/i?img=/i/headshots/nfl/players/full/{}.png'.format(eid)

                if not path.exists(normal_file):
                    try:
                        # download image and save as normal file
                        img_content = requests.get(img_url).content
                        with open(normal_file, 'wb') as f:
                            f.write(img_content)

                        # resize and saev as icon file
                        height = 24
                        img = Image.open(normal_file)
                        hpercent = (height / float(img.size[1]))
                        wsize = int((float(img.size[0]) * float(hpercent)))
                        img = img.resize((wsize, height), Image.ANTIALIAS)
                        img.save(icon_file) 
                    except Exception as e:
                        eid = -1

                Player.objects.filter(team=team, first_name=first_name, last_name=last_name).update(eid=eid)
        # except:
        #     print('*** Something is wrong ***')


if __name__ == "__main__":
    teams = Player.objects.all().values_list('team', flat=True).distinct()
    get_avatars(teams)
