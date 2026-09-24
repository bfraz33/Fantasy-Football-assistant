from espn_api.football import League
import json

#Loading parameter credentials
with open('config/parameters.json', 'r') as f:
    params = json.load(f)

league_id = params['league_id']
year = params['year']
espn_s2 = params['espn_s2']
swid = params['swid']

league = League(
    league_id=league_id,
    year=year,
    espn_s2=espn_s2,
    swid=swid
)

print("Connected to ESPN Fantasy Football League ID:", league_id, "for:", year)

# print("\nTeams in league:")

# #confirm connection to api and league, prints team names.
# for team in league.teams:
#     print(team.team_name)

