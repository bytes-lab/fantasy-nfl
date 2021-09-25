from django import template

from general.models import *

register = template.Library()

@register.filter
def div(val, de):
    if not de:
        return '-'
    return '{:.2f}'.format(val * 1.0 / de)

@register.filter
def div_pcnt(val, de):
    if not de:
        return '0.0'
    return '{:.2f}'.format(val * 100.0 / de)

@register.filter
def pdiff_color(team_stat):
    return 'text-danger' if team_stat['tyda'] < team_stat['tya'] else 'text-success'

@register.filter
def pdiff(team_stat):
    val = team_stat['tyda'] - team_stat['tya']
    fm = '{:.1f}' if val > 0 else '({:.1f})'
    return fm.format(abs(val))

@register.filter
def pdiff_pt_color(team_stat):
    a_val = team_stat['pa']
    s_val = team_stat['ps']

    return 'text-danger' if a_val < s_val else 'text-success'

@register.filter
def pdiff_pt(team_stat):
    val = team_stat['pa'] - team_stat['ps']
    fm = '{:.1f}' if val > 0 else '({:.1f})'
    return fm.format(abs(val))

@register.filter
def aya(player):
    if not player.pass_att:
        return '0.0'
    return '{:.2f}'.format((player.pass_yds + 20 * player.pass_td  - 45 * player.pass_int) * 1.0 / player.pass_att)

@register.filter()
def liked(uid, session):
    fav = session.get('fav', [])
    return 'done' if str(uid) in fav else ''

@register.filter
def sgr(s):
    return s.split(' ')[0]

@register.filter
def team(opponent):
    return opponent.strip('@')

@register.filter
def vs(opponent):
    return '@' if '@' in opponent else 'vs'

@register.filter
def cus_proj(player, session):
    cus_proj = session.get('cus_proj', {})
    return cus_proj.get(str(player.id), player.proj_points)
