import urllib2
import json
from itertools import groupby
from operator import itemgetter

# taken from http://stackoverflow.com/questions/1143671/python-sorting-list-of-dictionaries-by-multiple-keys with minor modifications
def multikeysort(items, columns):
    comparers = [ ((itemgetter(col[1:].strip()), -1) if col.startswith('-') else (itemgetter(col.strip()), 1)) for col in columns]
    def comparer(left, right):
        for fn, mult in comparers:
            result = cmp(float(fn(left)['$t']), float(fn(right)['$t']))
            if result:
                return mult * result
        else:
            return 0
    return sorted(items, cmp=comparer)

league_url = 'http://football26.myfantasyleague.com/2014/export?TYPE=league&L=17492&JSON=1'
franchise_json = json.loads(urllib2.urlopen(league_url).read())
franchises = franchise_json['league']['franchises']['franchise']
sorted_franchises = sorted(franchises, key=lambda k: k['division'])
grouped_franchises = groupby(sorted_franchises, lambda x: x['division'])
franchise_dict = {franchise['id']: franchise for franchise in franchises}

standings_url = 'http://football26.myfantasyleague.com/2014/export?TYPE=standings&L=17492&JSON=1'
standings_json = json.loads(urllib2.urlopen(standings_url).read())
standings = standings_json['standings']['franchise']

standings_dict = {}
for standing in standings:
  standings_dict[standing['id']] = standing

division_standings = {}
playoff_teams = []
for division, franchises in grouped_franchises:
  standings = []
  for franchise in franchises:
    standings.append(standings_dict[franchise['id']])
  sorted_standings = multikeysort(standings, ['-h2hw', '-pf'])
  for team in sorted_standings[:4]:
    playoff_teams.append(team['id'])

rosters_url = 'http://football26.myfantasyleague.com/2014/export?TYPE=rosters&L=17492&JSON=1'
rosters_json = json.loads(urllib2.urlopen(rosters_url).read())
rosters = rosters_json['rosters']['franchise']

playoff_players = {}
for roster in rosters:
  if roster['id'] in playoff_teams:
    players = roster['player']
    for player in players:
      try:
        playoff_players[player['id']] = playoff_players[player['id']] + 1
      except KeyError:
        playoff_players[player['id']] = 1

sorted_playoff_players = sorted(playoff_players.items(), key=itemgetter(1), reverse=True)

players_url = 'http://football.myfantasyleague.com/2014/export?TYPE=players&JSON=1'
players_json = json.loads(urllib2.urlopen(players_url).read())
players = players_json['players']['player']
players_dict = {player['id']: player['name'] for player in players}

with open('output', 'w') as f:
  f.write('Player Name|Percent Owned By Playoff Teams\n')
  f.write('---|---\n')
  for playoff_player in sorted_playoff_players:
    try:
      pct = (playoff_player[1] / 6.0) * 100
      f.write('{}|{:.2f}\n'.format(players_dict[playoff_player[0]], pct))
    except KeyError:
      f.write('Player id {}|{:.2f}\n'.format(playoff_player[0], pct))
