DATA_SOURCE = (
    ('DraftKings', 'DraftKings'),
    ('FanDuel', 'FanDuel'),
    ('Yahoo', 'Yahoo'),
    ('Fanball', 'Fanball')
)


POSITION_LIMITS_ = [
    ["QB", 1, 1],
    ["RB", 2, 3],
    ["WR", 3, 4],
    ["TE", 1, 2],
    ["DEF", 1, 1],
    ["RB,WR,TE", 7, 7]
]


POSITION_LIMITS = {
    'FanDuel': [
                   ["QB", 1, 1],
                   ["RB", 2, 2],
                   ["WR", 2, 2],
                   ["TE", 2, 2],
                   ["DEF", 1, 1]
               ],
    'DraftKings': [
                      ["QB", 1, 1],
                      ["RB", 2, 3],
                      ["WR", 3, 4],
                      ["TE", 1, 2],
                      ["DEF", 1, 1],
                      ["RB,WR,TE", 7, 7]
                  ],
    'Yahoo': [
                ["QB", 1, 3],
                ["RB", 1, 3],
                ["WR", 1, 3],
                ["TE", 1, 3],
                ["DEF", 1, 2],
                ["QB,RB", 3, 4],
                ["WR,TE", 3, 4]
            ],
    'Fanball': [
                ["QB", 1, 3],
                ["RB", 1, 3],
                ["WR", 1, 3],
                ["TE", 1, 3],
                ["DEF", 1, 3],
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


POSITION = ['QB', 'RB', 'WR', 'TE', 'DEF']
