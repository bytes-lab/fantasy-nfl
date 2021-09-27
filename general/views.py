# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import os
import json
import mimetypes
import datetime
from wsgiref.util import FileWrapper

from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.template.loader import render_to_string
from django.utils.encoding import smart_str
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Avg, Q

from general.models import *
from general.lineup import *
from general.color import *
from general.utils import *
from general.constants import DATA_SOURCE, POSITION


def _get_game_today():
    return Game.objects.all()


def _all_teams():
    return [ii['team'] for ii in Player.objects.values('team').distinct()]


def players(request):
    players = Player.objects.filter(data_source='FanDuel').order_by('first_name')
    return render(request, 'players.html', locals())


def lineup(request):
    data_sources = DATA_SOURCE
    games = _get_game_today()
    return render(request, 'lineup.html', locals())


@csrf_exempt
def fav_player(request):
    uid = request.POST.get('uid')
    if uid:
        if uid == "-1":
            request.session['fav'] = []
        else:
            fav = request.session.get('fav', [])
            if uid in fav:
                fav.remove(uid)
            else:
                fav.append(uid)
            request.session['fav'] = fav

    fav = request.session.get('fav', [])
    players = [Player.objects.filter(uid=uid).first() for uid in fav]
    players = sorted(players, key=Roster().position_order)

    return HttpResponse(render_to_string('fav-body.html', locals()))


@csrf_exempt
def get_players(request):
    ds = request.POST.get('ds')
    teams = request.POST.get('games').strip(';').replace(';', '-').split('-')
    players = Player.objects.filter(data_source=ds, 
                                    team__in=teams,
                                    available=True) \
                            .order_by('-proj_points')
    return HttpResponse(render_to_string('player-list_.html', locals()))


def get_games_(pid, loc, opp, season):
    player = Player.objects.get(id=pid)
    q = Q(name='{} {}'.format(player.first_name, player.last_name)) \
      & Q(date__range=[datetime.date(season, 9, 1), datetime.date(season, 12, 31)])

    if opp:
        q &= Q(opp=opp)
    if loc != 'all':
        q &= Q(game_location=loc)

    return PlayerGame.objects.filter(q).order_by('-date')


def current_season():
    today = datetime.date.today()
    return today.year if today > datetime.date(today.year, 9, 1) else today.year - 1


def player_detail(request, pid):
    player = Player.objects.get(id=pid)
    year = current_season()
    games = get_games_(pid, 'all', '', year)
    avg_fpts = games.aggregate(Avg('fpts'))

    return render(request, 'player_detail.html', locals())


@csrf_exempt
def player_games(request):
    pid = request.POST.get('pid')
    loc = request.POST.get('loc')
    opp = request.POST.get('opp')
    season = int(request.POST.get('season'))

    games = get_games_(pid, loc, opp, season)

    opps = '<option value="">All</option>'
    for ii in sorted(set(games.values_list('opp', flat=True).distinct())):
        opps += '<option>{}</option>'.format(ii)

    player = Player.objects.get(id=pid)
    template = 'game-list_def.html' if player.position == 'DEF' else 'game-list_.html'

    result = {
        'game_table': render_to_string(template, locals()),
        'chart': [[ii.date.strftime('%Y/%m/%d'), ii.fpts] for ii in games],
        'opps': opps
    }

    return JsonResponse(result, safe=False)


def player_match_up_board(request):
    games = _get_game_today()
    return render(request, 'player-match-up-board.html', locals())


def get_ranking(players, sattr, dattr, order=1):
    # order = 1: ascending, -1: descending
    players = sorted(players, key=lambda k: k[sattr]*order)
    ranking = 0
    prev_val = None
    for ii in players:
        if ii[sattr] != prev_val:
            prev_val = ii[sattr]
            ranking += 1
        ii[dattr] = ranking
    return players, ranking


def get_team_stat(team):
    season = current_season()
    # defense allowance
    ## for overall
    q = Q(team=team) & Q(pos='DEF') & \
        Q(date__range=[datetime.date(season, 9, 1), datetime.date(season, 12, 31)])
    a_teams = PlayerGame.objects.filter(q)

    tyda = a_teams.aggregate(Avg('pass_long'))['pass_long__avg'] or 0 
    pyda = a_teams.aggregate(Avg('pass_sacked_yds'))['pass_sacked_yds__avg'] or 0
    ruyda = a_teams.aggregate(Avg('pass_yds_per_att'))['pass_yds_per_att__avg'] or 0

    ## last game
    a_teams_ = a_teams.order_by('-date').first()

    l_tya = a_teams_.pass_long
    l_pya = a_teams_.pass_sacked_yds
    l_ruya = a_teams_.pass_yds_per_att

    ## allowed points
    pa = a_teams.aggregate(Avg('pass_att'))['pass_att__avg'] or 0

    ## home
    ha_teams = a_teams.filter(game_location='')

    h_tyda = ha_teams.aggregate(Avg('pass_long'))['pass_long__avg'] or 0 
    h_pya = ha_teams.aggregate(Avg('pass_sacked_yds'))['pass_sacked_yds__avg'] or 0
    h_ruya = ha_teams.aggregate(Avg('pass_yds_per_att'))['pass_yds_per_att__avg'] or 0

    ## away
    aa_teams = a_teams.filter(game_location='@')

    a_tyda = aa_teams.aggregate(Avg('pass_long'))['pass_long__avg'] or 0 
    a_pya = aa_teams.aggregate(Avg('pass_sacked_yds'))['pass_sacked_yds__avg'] or 0
    a_ruya = aa_teams.aggregate(Avg('pass_yds_per_att'))['pass_yds_per_att__avg'] or 0

    # offense    

    ## home
    h_py = ha_teams.aggregate(Avg('pass_td'))['pass_td__avg'] or 0
    h_ruy = ha_teams.aggregate(Avg('pass_int'))['pass_int__avg'] or 0

    ## away
    a_py = aa_teams.aggregate(Avg('pass_td'))['pass_td__avg'] or 0
    a_ruy = aa_teams.aggregate(Avg('pass_int'))['pass_int__avg'] or 0

    ## overall
    tya = a_teams.aggregate(Avg('pass_yds'))['pass_yds__avg'] or 0 
    pya = a_teams.aggregate(Avg('pass_td'))['pass_td__avg'] or 0
    ruya = a_teams.aggregate(Avg('pass_int'))['pass_int__avg'] or 0
    
    ## last game
    l_py = a_teams_.pass_td
    l_ruy = a_teams_.pass_int

    ## scored points
    ps = a_teams.aggregate(Avg('pass_cmp'))['pass_cmp__avg'] or 0

    res = {
        'team': team,

        'tyda': tyda,
        'pyda': pyda,
        'ruyda': ruyda,
        'pa': pa, 

        'l_tya': l_tya,
        'l_pya': l_pya,
        'l_ruya': l_ruya,

        'h_tyda': h_tyda,
        'h_pya': h_pya,
        'h_ruya': h_ruya,

        'a_tyda': a_tyda,
        'a_pya': a_pya,
        'a_ruya': a_ruya,

        'tya': tya,
        'pya': pya,
        'ruya': ruya,
        'ps': ps,

        'h_py': h_py,
        'h_ruy': h_ruy,

        'a_py': a_py,
        'a_ruy': a_ruy,

        'l_py': l_py,
        'l_ruy': l_ruy,
    }

    return res


def get_player(full_name, team):
    '''
    FanDuel has top priority
    '''
    names = full_name.split(' ')
    players = Player.objects.filter(first_name=names[0], last_name=names[1], team=team) \
                            .order_by('data_source')
    player = players.filter(data_source='FanDuel').first()
    if not player:
        player = players.first()
    return player


def build_player_cache():
    # player info -> build cache
    season = current_season()
    ## for players
    players = Player.objects.filter(data_source='FanDuel', available=True) \
                            .exclude(position='DEF')

    yds_field_dict = { 'QB': 'pass_yds', 'RB': 'rush_yds', 'WR': 'rec_yds', 'TE': 'rec_yds' }
    for player in players:
        games = get_games_(player.id, 'all', '', season)
        afp = games.aggregate(Avg('fpts'))['fpts__avg'] or 0

        yoa = 0
        if player.position in yds_field_dict:
            field = yds_field_dict[player.position]
            yoa = games.aggregate(Avg(field))[field+'__avg'] or 0

        Player.objects.filter(uid=player.uid).update(
            afp=afp,
            yoa=yoa
        )


@csrf_exempt
def player_match_up(request):
    pos = request.POST.get('pos')
    ds = request.POST.get('ds')
    games = request.POST.get('games').strip(';').split(';')

    order = request.POST.get('order')
    if not order:
        order = 'pyda_rank' if pos in ['QB', 'WR', 'TE'] else 'ruyda_rank' if pos in ['RB'] else 'ps'

    reverse = False if '-' in order else True
    order = order.replace('-', '')

    game_info = {}
    teams_ = []
    for game in games:
        if not game:
            continue
        teams = game.split('-') # home-away
        game_info[teams[0]] = [teams[1], '', '@']   # vs, loc, loc_
        game_info[teams[1]] = [teams[0], '@', '']

        teams_.append(teams[0])
        teams_.append(teams[1])

    players = Player.objects.filter(data_source=ds, available=True, team__in=teams_) \
                            .order_by('-proj_points')
    players_ = []

    team_stat = json.loads(TMSCache.objects.filter(team='TEAM STAT', type=1).first().body)
    for player in players:
        if pos in player.position:
            vs = game_info[player.team][0]
            loc = game_info[player.team][1]

            p = {
                'id': player.id,
                'uid': player.uid,
                'eid': player.eid,
                'name': '{} {}'.format(player.first_name, player.last_name),
                'team': player.team,
                'loc': loc,
                'vs': vs,
                'inj': player.injury,
                'salary': player.salary,
                'afp': player.afp,
                'yoa': player.yoa,
                'val': player.value
            }

            p.update(team_stat[player.team])
            players_.append(p)

    players, _ = get_ranking(players_, 'afp', 'ppr', -1)

    players = sorted(players, key=lambda k: k[order], reverse=reverse)
    template = 'player-board-{}.html'.format(pos.lower())

    return HttpResponse(render_to_string(template, locals()))


def mean(numbers):
    return float(sum(numbers)) / max(len(numbers), 1)


def _get_lineups(request):
    ids = request.POST.getlist('ids')
    locked = request.POST.getlist('locked')
    num_lineups = int(request.POST.get('num-lineups'))
    ds = request.POST.get('ds')

    ids = [int(ii) for ii in ids]
    locked = [int(ii) for ii in locked]

    players = Player.objects.filter(id__in=ids, proj_points__gt=0)
    lineups = calc_lineups(players, num_lineups, locked, ds)
    return lineups, players


def get_num_lineups(player, lineups):
    num = 0
    for ii in lineups:
        if ii.is_member(player):
            num = num + 1
    return num


def gen_lineups(request):
    lineups, players = _get_lineups(request)
    avg_points = mean([ii.projected() for ii in lineups])

    players_ = [{ 'name': '{} {}'.format(ii.first_name, ii.last_name), 
                  'team': ii.team, 
                  'id': ii.id, 
                  'eid': ii.eid, 
                  'position': ii.position,
                  'first_name': ii.first_name,
                  'lineups': get_num_lineups(ii, lineups)} 
                for ii in players if get_num_lineups(ii, lineups)]
    players_ = sorted(players_, key=lambda k: k['lineups'], reverse=True)
    return HttpResponse(render_to_string('player-lineup.html', locals()))


def export_lineups(request):
    lineups, _ = _get_lineups(request)
    ds = request.POST.get('ds')
    csv_fields = ['QB', 'RB', 'RB', 'WR', 'WR', 'WR', 'TE', 'FLEX', 'DST']
    path = "/tmp/.fantasy_nfl_{}.csv".format(ds.lower())

    with open(path, 'w') as f:
        f.write(','.join(csv_fields)+'\n')
        for ii in lineups:
            f.write(ii.get_csv(ds))
    
    wrapper = FileWrapper( open( path, "r" ) )
    content_type = mimetypes.guess_type( path )[0]

    response = HttpResponse(wrapper, content_type = content_type)
    response['Content-Length'] = os.path.getsize( path ) # not FileField instance
    response['Content-Disposition'] = 'attachment; filename=%s' % smart_str( os.path.basename( path ) ) # same here        
    return response


@csrf_exempt
def update_point(request):
    pid = int(request.POST.get('pid'))
    points = request.POST.get('val')

    player = Player.objects.get(id=pid)
    cus_proj = request.session.get('cus_proj', {})
    cus_proj[pid] = points
    request.session['cus_proj'] = cus_proj

    return HttpResponse('')


def download_game_report(request):
    game = request.GET.get('game')
    game = Game.objects.get(id=game)
    season = current_season() - 1
    q = Q(team__in=[game.home_team, game.visit_team]) & \
        Q(opp__in=[game.home_team, game.visit_team]) & \
        Q(date__range=[datetime.date(season, 9, 1), datetime.date(season, 12, 31)])
    qs = PlayerGame.objects.filter(q)
    fields = [f.name for f in PlayerGame._meta.get_fields() 
              if f.name not in ['id', 'uid', 'updated_at', 'created_at']]
    path = "/tmp/nfl_games({}@{}).csv".format(game.visit_team, game.home_team)
    return download_response(qs, path, fields)


def build_TMS_cache():
    all_teams = _all_teams()
    colors = linear_gradient('#90EE90', '#137B13', len(all_teams))['hex']

    team_stat = [get_team_stat(ii) for ii in all_teams]

    for attr in ['pyda', 'ruyda']:
        team_stat, _ = get_ranking(team_stat, attr, attr+'_rank')
        for ii in team_stat:
            ii[attr+'_color'] = colors[ii[attr+'_rank']-1]

    team_info = { ii['team']: ii for ii in team_stat }

    TMSCache.objects.all().delete()
    TMSCache.objects.create(team='TEAM STAT', type=1, body=json.dumps(team_info))
