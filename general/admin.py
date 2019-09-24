# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

from rangefilter.filter import DateRangeFilter

from general.models import *
from general.utils import *

class PlayerAdmin(admin.ModelAdmin):
    list_display = ['uid', 'eid', 'first_name', 'last_name', 'position', 'team', 'opponent', 'salary', 
                    'proj_points', 'available', 'data_source', 'updated_at', 'created_at']
    search_fields = ['first_name', 'last_name', 'team', 'uid']
    list_filter = ['data_source', 'position', 'available', 'team']


class PlayerGameAdmin(admin.ModelAdmin):
    list_display = ['name', 'uid', 'pos', 'team', 'game_location', 'opp', 'game_result', 'fpts', 'date']
    search_fields = ['name']
    list_filter = [('date', DateRangeFilter), 'game_location', 'pos', 'team', 'opp']
    actions = ['export_games']

    def export_games(self, request, queryset):
        fields = [f.name for f in PlayerGame._meta.get_fields() 
                  if f.name not in ['id', 'is_new']]
        path = "/tmp/nba_games.csv"

        return download_response(queryset, path, fields)

    export_games.short_description = "Export CSV" 


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
