# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models

from general.constants import DATA_SOURCE


class Player(models.Model):
    uid = models.IntegerField()
    eid = models.IntegerField(default=-1)               # espn id for avatar
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    injury = models.CharField(max_length=250, blank=True, null=True)
    opponent = models.CharField(max_length=50)
    exp = models.IntegerField(default=0)                # for exceptional avatar
    
    position = models.CharField(max_length=50)
    proj_points = models.FloatField(default=0)
    proj_site = models.FloatField(default=0)
    salary = models.IntegerField(default=0)

    yoa = models.FloatField(default=0)
    afp = models.FloatField(default=0)

    salary_original = models.FloatField(default=0)
    team = models.CharField(max_length=50)
    value = models.FloatField(default=0)
    
    available = models.BooleanField(default=False)
    data_source = models.CharField(max_length=30, choices=DATA_SOURCE, default='FanDuel')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return '{} {}'.format(self.first_name, self.last_name)


class PlayerGame(models.Model):
    name = models.CharField(max_length=50)
    uid = models.CharField(max_length=50)

    team = models.CharField("Tm", max_length=10)
    game_location = models.CharField("H-A", max_length=5)
    opp = models.CharField("Vs", max_length=10)
    game_result = models.CharField("W-L", max_length=15)
    pos = models.CharField(max_length=5)

    pass_cmp = models.IntegerField(default=0)       # offense score - DEF
    pass_att = models.IntegerField(default=0)       # defense score - DEF
    pass_cmp_perc = models.FloatField(default=0)    # offense 1st down - DEF
    pass_yds = models.IntegerField(default=0)       # offense total yards - DEF
    pass_td = models.IntegerField(default=0)        # offense passing yards - DEF
    pass_int = models.IntegerField(default=0)       # offense rushing yards - DEF
    pass_rating = models.FloatField(default=0)      # offense turnover lost - DEF
    pass_sacked = models.IntegerField(default=0)        # defense 1st down - DEF
    pass_long = models.IntegerField(default=0)          # defense total yards - DEF
    pass_sacked_yds = models.IntegerField(default=0)    # defense passing yards - DEF
    pass_yds_per_att = models.FloatField(default=0)     # defense rushing yards - DEF
    pass_adj_yds_per_att = models.FloatField(default=0) # defense turnover lost - DEF
    rush_att = models.IntegerField(default=0)
    rush_yds = models.IntegerField(default=0)
    rush_yds_per_att = models.FloatField(null=True, blank=True)
    rush_td = models.IntegerField(default=0)
    rush_long = models.IntegerField(default=0)
    targets = models.IntegerField(default=0)
    rec = models.IntegerField(default=0)
    rec_yds = models.IntegerField(default=0)
    rec_yds_per_rec = models.FloatField(null=True, blank=True)
    rec_td = models.IntegerField(default=0)
    rec_long = models.IntegerField(default=0)
    catch_pct = models.FloatField(default=0)
    rec_yds_per_tgt = models.FloatField(null=True, blank=True)
    fumbles = models.IntegerField(default=0)
    fumbles_lost = models.IntegerField(default=0)
    week_num = models.IntegerField()

    date = models.DateField()
    fpts = models.FloatField("FPTS", default=-1)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


GAME_STATUS = (
    ('started', 'Started'),
    ('upcoming', 'Upcomming')
)

class Game(models.Model):
    home_team = models.CharField(max_length=20)
    visit_team = models.CharField(max_length=20)
    ou = models.FloatField(default=0)
    ml = models.CharField(max_length=20)
    date = models.CharField(max_length=30)

    def __str__(self):
        return '{} - {}'.format(self.home_team, self.visit_team)


# Team Matchup Sheet Cache
class TMSCache(models.Model):
    team = models.CharField(max_length=10)
    type = models.IntegerField()
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.team
