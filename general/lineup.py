import operator as op
from ortools.linear_solver import pywraplp
from general.models import *
import pdb


class Roster:
    POSITION_ORDER = {
        "QB": 0,
        "RB": 1,
        "WR": 2,
        "TE": 3,
        "D": 4
    }

    def __init__(self):
        self.players = []

    def add_player(self, player):
        self.players.append(player)

    def is_member(self, player):
        return player in self.players

    def get_num_teams(self):
        teams = set([ii.team for ii in self.players])
        return len(teams)

    def spent(self):
        return sum(map(lambda x: x.salary, self.players))

    def projected(self):
        return sum(map(lambda x: x.proj_points, self.players))

    def position_order(self, player):
        return self.POSITION_ORDER[player.position]

    def dict_position_order(self, player):
        if player['pos'] in self.POSITION_ORDER:
            return self.POSITION_ORDER[player['pos']] + 10.0 / player['salary']
        else:
            return 100

    def sorted_players(self):
        return sorted(self.players, key=self.position_order)

    def get_csv(self, ds):
        s = ''
        pos = ['QB', 'RB', 'RB', 'WR', 'WR', 'WR', 'TE', 'RB,WR,TE', 'DST']
        players = list(self.players)
        for ii in pos:
            for jj in players:
                if jj.position in ii:
                    s += str(jj) + ','
                    players.remove(jj)
                    break
        return s + '\n'

    def __repr__(self):
        s = '\n'.join(str(x) for x in self.sorted_players())
        s += "\n\nProjected Score: %s" % self.projected()
        s += "\tCost: $%s" % self.spent()
        return s


POSITION_LIMITS_ = [
    ["QB", 1, 1],
    ["RB", 2, 3],
    ["WR", 3, 4],
    ["TE", 1, 2],
    ["D", 1, 1],
    ["RB,WR,TE", 7, 7]
]
               
POSITION_LIMITS = {
    'FanDuel': [
                   ["QB", 1, 1],
                   ["RB", 2, 2],
                   ["WR", 2, 2],
                   ["TE", 2, 2],
                   ["D", 1, 1]
               ],
    'DraftKings': [
                      ["QB", 1, 1],
                      ["RB", 2, 3],
                      ["WR", 3, 4],
                      ["TE", 1, 2],
                      ["D", 1, 1],
                      ["RB,WR,TE", 7, 7]
                  ],
    'Yahoo': [
                ["QB", 1, 3],
                ["RB", 1, 3],
                ["WR", 1, 3],
                ["TE", 1, 3],
                ["D", 1, 2],
                ["QB,RB", 3, 4],
                ["WR,TE", 3, 4]
            ],
    'Fanball': [
                ["QB", 1, 3],
                ["RB", 1, 3],
                ["WR", 1, 3],
                ["TE", 1, 3],
                ["D", 1, 3],
                ["QB,RB", 3, 4],
                ["WR,TE", 3, 4]
            ]
}

SALARY_CAP = {
    'FanDuel': 60000,
    'DraftKings': 50000,
    'Yahoo': 200,
    'Fanball': 55000
}

ROSTER_SIZE = {
    'FanDuel': 9,
    'DraftKings': 9,
    'Yahoo': 9,
    'Fanball': 9
}


def get_lineup(ds, players, teams, locked, max_point):
    solver = pywraplp.Solver('nfl-lineup', pywraplp.Solver.CBC_MIXED_INTEGER_PROGRAMMING)

    variables = []

    for player in players:
        if player.id in locked:
            variables.append(solver.IntVar(1, 1, str(player)))
        else:        
            variables.append(solver.IntVar(0, 1, str(player)))

    objective = solver.Objective()
    objective.SetMaximization()

    for i, player in enumerate(players):
        objective.SetCoefficient(variables[i], player.proj_points)

    salary_cap = solver.Constraint(0, SALARY_CAP[ds])
    for i, player in enumerate(players):
        salary_cap.SetCoefficient(variables[i], player.salary)

    point_cap = solver.Constraint(0, max_point)
    for i, player in enumerate(players):
        point_cap.SetCoefficient(variables[i], player.proj_points)

    position_limits = POSITION_LIMITS[ds]
    for position, min_limit, max_limit in POSITION_LIMITS_:
        position_cap = solver.Constraint(min_limit, max_limit)

        for i, player in enumerate(players):
            if player.position in position:
                position_cap.SetCoefficient(variables[i], 1)

    # at most 6 players from one team (yahoo)
    for team in teams:
        team_cap = solver.Constraint(0, 6)
        for i, player in enumerate(players):
            if team == player.team:
                team_cap.SetCoefficient(variables[i], 1)

    size_cap = solver.Constraint(ROSTER_SIZE[ds], ROSTER_SIZE[ds])
    for variable in variables:
        size_cap.SetCoefficient(variable, 1)

    # pdb.set_trace()
    solution = solver.Solve()

    if solution == solver.OPTIMAL:
        roster = Roster()

        for i, player in enumerate(players):
            if variables[i].solution_value() == 1:
                roster.add_player(player)

        return roster


def calc_lineups(players, num_lineups, locked=[], ds='FanDuel'):
    result = []

    max_point = 10000
    teams = set([ii.team for ii in players])
    # pdb.set_trace()
    while True:
        # add condition projection > 0
        roster = get_lineup(ds, players, teams, locked, max_point)
        max_point = roster.projected() - 0.001

        if not roster:
            break
        
        if roster.get_num_teams() > 2 or ds != 'Yahoo': # min number of teams - 3 (Yahoo)
            result.append(roster)
            if len(result) == num_lineups:
                break

    return result
