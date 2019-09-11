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
from django.db.models import Avg, Q, Sum

from general.models import *
from general.lineup import *
from general.color import *

POSITION = ['QB', 'RB', 'WR', 'TE', 'DEF']
POSITION_GAME_MAP = {'QB': ['QB'], 'RB': ['RB', 'FB'], 'WR': ['WR'], 'TE': ['TE']}

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
    return today.year if today > datetime.date(today.year, 9, 19) else today.year - 1


def player_detail(request, pid):
    player = Player.objects.get(id=pid)
    year = current_season()
    games = get_games_(pid, 'all', '', year)
    avg_fpts = games.aggregate(Avg('fpts'))
    year = 2019

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

    result = {
        'game_table': render_to_string('game-list_.html', locals()),
        'chart': [[ii.date.strftime('%Y/%m/%d'), ii.fpts] for ii in games],
        'opps': opps
    }

    return JsonResponse(result, safe=False)


def player_match_up_board(request):
    games = _get_game_today()
    return render(request, 'player-match-up-board.html', locals())


def formatted_diff(val):
    fm = '{:.1f}' if val > 0 else '({:.1f})'
    return fm.format(abs(val))


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
    q = Q(opp=team)& \
        Q(date__range=[datetime.date(season, 9, 1), datetime.date(season, 12, 31)])
    a_teams = PlayerGame.objects.filter(q)
    a_teams_ = a_teams.values('date').annotate(pass_yds=Sum('pass_yds'), 
                                               rush_yds=Sum('rush_yds'),
                                               rec_yds=Sum('rec_yds'))

    pyda = a_teams_.aggregate(Avg('pass_yds'))['pass_yds__avg'] or 0
    ruyda = a_teams_.aggregate(Avg('rush_yds'))['rush_yds__avg'] or 0
    rcyda = a_teams_.aggregate(Avg('rec_yds'))['rec_yds__avg'] or 0

    ## last game
    a_teams_ = a_teams_.order_by('-date').first()

    l_pya = a_teams_.get('pass_yds') or 0
    l_ruya = a_teams_.get('rush_yds') or 0
    l_rcya = a_teams_.get('rec_yds') or 0

    ## allowed points
    q = Q(opp=team) & Q(pos='DEF') & \
        Q(date__range=[datetime.date(season, 9, 1), datetime.date(season, 12, 31)])
    a_teams = PlayerGame.objects.filter(q)
    pa = a_teams.aggregate(Avg('fpts'))['fpts__avg'] or 0

    loc = ''        ## home
    q = Q(opp=team) & Q(game_location=loc) & \
        Q(date__range=[datetime.date(season, 9, 1), datetime.date(season, 12, 31)])
    a_teams = PlayerGame.objects.filter(q)
    a_teams_ = a_teams.values('date').annotate(pass_yds=Sum('pass_yds'), 
                                               rush_yds=Sum('rush_yds'),
                                               rec_yds=Sum('rec_yds'))

    h_pya = a_teams_.aggregate(Avg('pass_yds'))['pass_yds__avg'] or 0
    h_ruya = a_teams_.aggregate(Avg('rush_yds'))['rush_yds__avg'] or 0
    h_rcya = a_teams_.aggregate(Avg('rec_yds'))['rec_yds__avg'] or 0

    loc = '@'        ## home
    q = Q(opp=team) & Q(game_location=loc) & \
        Q(date__range=[datetime.date(season, 9, 1), datetime.date(season, 12, 31)])
    a_teams = PlayerGame.objects.filter(q)
    a_teams_ = a_teams.values('date').annotate(pass_yds=Sum('pass_yds'), 
                                               rush_yds=Sum('rush_yds'),
                                               rec_yds=Sum('rec_yds'))

    a_pya = a_teams_.aggregate(Avg('pass_yds'))['pass_yds__avg'] or 0
    a_ruya = a_teams_.aggregate(Avg('rush_yds'))['rush_yds__avg'] or 0
    a_rcya = a_teams_.aggregate(Avg('rec_yds'))['rec_yds__avg'] or 0

    # offense    
    loc = ''        ## home
    q = Q(team=team) & Q(game_location=loc) & \
        Q(date__range=[datetime.date(season, 9, 1), datetime.date(season, 12, 31)])
    s_teams = PlayerGame.objects.filter(q)
    s_teams_ = s_teams.values('date').annotate(pass_yds=Sum('pass_yds'), 
                                               rush_yds=Sum('rush_yds'),
                                               rec_yds=Sum('rec_yds'))

    h_py = s_teams_.aggregate(Avg('pass_yds'))['pass_yds__avg'] or 0
    h_ruy = s_teams_.aggregate(Avg('rush_yds'))['rush_yds__avg'] or 0
    h_rcy = s_teams_.aggregate(Avg('rec_yds'))['rec_yds__avg'] or 0

    loc = '@'       ## away
    q = Q(team=team) & Q(game_location=loc) & \
        Q(date__range=[datetime.date(season, 9, 1), datetime.date(season, 12, 31)])
    s_teams = PlayerGame.objects.filter(q)
    s_teams_ = s_teams.values('date').annotate(pass_yds=Sum('pass_yds'), 
                                               rush_yds=Sum('rush_yds'),
                                               rec_yds=Sum('rec_yds'))

    a_py = s_teams_.aggregate(Avg('pass_yds'))['pass_yds__avg'] or 0
    a_ruy = s_teams_.aggregate(Avg('rush_yds'))['rush_yds__avg'] or 0
    a_rcy = s_teams_.aggregate(Avg('rec_yds'))['rec_yds__avg'] or 0

    ## overall
    q = Q(team=team) & \
        Q(date__range=[datetime.date(season, 9, 1), datetime.date(season, 12, 31)])
    s_teams = PlayerGame.objects.filter(q)
    s_teams_ = s_teams.values('date').annotate(pass_yds=Sum('pass_yds'), 
                                               rush_yds=Sum('rush_yds'),
                                               rec_yds=Sum('rec_yds'))

    pya = s_teams_.aggregate(Avg('pass_yds'))['pass_yds__avg'] or 0
    ruya = s_teams_.aggregate(Avg('rush_yds'))['rush_yds__avg'] or 0
    rcya = s_teams_.aggregate(Avg('rec_yds'))['rec_yds__avg'] or 0
    
    ## last game
    s_teams_ = s_teams_.order_by('-date').first()

    l_py = s_teams_.get('pass_yds') or 0
    l_ruy = s_teams_.get('rush_yds') or 0
    l_rcy = s_teams_.get('rec_yds') or 0

    ## scored points
    q = Q(team=team) & Q(pos='DEF') & \
        Q(date__range=[datetime.date(season, 9, 1), datetime.date(season, 12, 31)])
    s_teams = PlayerGame.objects.filter(q)
    ps = s_teams.aggregate(Avg('fpts'))['fpts__avg'] or 0

    res = {
        'team': team,
        'pyda': pyda,
        'ruyda': ruyda,
        'rcyda': rcyda,
        'pa': pa, 

        'l_pya': l_pya,
        'l_ruya': l_ruya,
        'l_rcya': l_rcya,

        'h_pya': h_pya,
        'h_ruya': h_ruya,
        'h_rcya': h_rcya,

        'a_pya': a_pya,
        'a_ruya': a_ruya,
        'a_rcya': a_rcya,

        'pya': pya,
        'ruya': ruya,
        'rcya': rcya,
        'ps': ps,

        'h_py': h_py,
        'h_ruy': h_ruy,
        'h_rcy': h_rcy,

        'a_py': a_py,
        'a_ruy': a_ruy,
        'a_rcy': a_rcy,

        'l_py': l_py,
        'l_ruy': l_ruy,
        'l_rcy': l_rcy
    }

    # FPA TM POS
    tm_pos = []
    # for each distinct match
    for ii in a_teams_:
        # players (games) in a match
        players = a_teams.filter(date=ii['date'])

        tm_pos_ = {}
        # for each position
        for pos in POSITION_GAME_MAP:
            tm_pos_[pos] = players.filter(pos__in=POSITION_GAME_MAP[pos]).aggregate(Sum('fpts'))['fpts__sum'] or 0

        if tm_pos_['QB'] > 0 and tm_pos_['RB'] > 0:
            tm_pos.append(tm_pos_)

    for pos in POSITION_GAME_MAP:
        res[pos] = sum(ii[pos] for ii in tm_pos) / len(tm_pos) if len(tm_pos) else -1

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


def get_win_loss(team):
    season = current_season()
    q = Q(team=team) & \
        Q(date__range=[datetime.date(season, 9, 1), datetime.date(season, 12, 31)])

    team_games = PlayerGame.objects.filter(q)
    game_results = team_games.values('date', 'game_result').distinct()
    wins = game_results.filter(game_result='W').count()
    losses = game_results.filter(game_result='L').count()
    return wins, losses


def filter_players_fpa(team, min_afp, max_afp):
    try:
        info = json.loads(TMSCache.objects.filter(team=team, type=1).first().body)
        players = []

        for ii in range(len(info['players'])):
            afp = info['players'][ii]['afp']
            if min_afp <= afp <= max_afp:
                players.append(info['players'][ii])
        info['players'] = players
        return info
    except Exception as e:
        return {}


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

    ## for DEF, get afp -> allowance
    teams = Player.objects.filter(data_source='FanDuel', available=True, position='DEF')
    for team in teams:
        q = Q(opp=team.team)& \
            Q(date__range=[datetime.date(season, 9, 1), datetime.date(season, 12, 31)])
        a_teams = PlayerGame.objects.filter(q)
        a_teams_ = a_teams.values('date').annotate(fpts=Sum('fpts'))
        fpa = a_teams_.aggregate(Avg('fpts'))['fpts__avg'] or 0

        Player.objects.filter(uid=team.uid).update(afp=fpa)


@csrf_exempt
def player_match_up(request):
    pos = request.POST.get('pos')
    ds = request.POST.get('ds')
    f_loc = request.POST.get('loc')
    games = request.POST.get('games').strip(';').split(';')
    order = request.POST.get('order') or pos+'_rank'

    reverse = False if '-' in order else True
    order = order.replace('-', '')

    game_info = {}
    teams_ = []
    for game in games:
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

            if loc == f_loc or f_loc == 'all':
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
                    'val': player.salary / 250 + 10
                }

                p.update(team_stat[player.team])
                players_.append(p)

    players, _ = get_ranking(players_, 'afp', 'ppr', -1)

    if order == 'DEF_rank':
        order = 'ps'

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


def build_TMS_cache():
    all_teams = _all_teams()
    colors = linear_gradient('#90EE90', '#137B13', len(all_teams))['hex']

    team_stat = [get_team_stat(ii) for ii in all_teams]
    for attr in POSITION_GAME_MAP:
        team_stat, _ = get_ranking(team_stat, attr, attr+'_rank')
        for ii in team_stat:
            ii[attr+'_color'] = colors[ii[attr+'_rank']-1]

    team_info = { ii['team']: ii for ii in team_stat }

    TMSCache.objects.all().delete()
    TMSCache.objects.create(team='TEAM STAT', type=1, body=json.dumps(team_info))
