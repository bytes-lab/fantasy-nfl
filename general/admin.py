# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

from general.models import *

class PlayerAdmin(admin.ModelAdmin):
    list_display = ['uid', 'eid', 'first_name', 'last_name', 'position', 'team', 'opponent', 'salary', 
                    'proj_points', 'available', 'data_source', 'updated_at', 'created_at']
    search_fields = ['first_name', 'last_name', 'team', 'uid']
    list_filter = ['team', 'data_source', 'position', 'available']


class PlayerGameAdmin(admin.ModelAdmin):
    list_display = ['name', 'uid', 'pos', 'team', 'game_location', 'opp', 'game_result', 'fpts', 'date']
    search_fields = ['name', 'team']
    list_filter = ['team', 'opp', 'game_location']


class GameAdmin(admin.ModelAdmin):
    list_display = ['home_team', 'visit_team', 'ou', 'ml', 'game_status', 'date']
    search_fields = ['home_team', 'visit_team']
    list_filter = ['game_status']


class TMSCacheAdmin(admin.ModelAdmin):
    list_display = ['team', 'type', 'created_at']


admin.site.register(Player, PlayerAdmin)
admin.site.register(PlayerGame, PlayerGameAdmin)
admin.site.register(Game, GameAdmin)
admin.site.register(TMSCache, TMSCacheAdmin)
