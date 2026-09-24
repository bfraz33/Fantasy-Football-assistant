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

#All teams in league
print("\nTeams in league:")

#confirm connection to api and league, prints team names.
for team in league.teams:
    print(team.team_name)
    print(team.team_id)

#Roster
print("\nMy Roster:")
for t in league.teams:
    if t.team_id == 44:
        for p in t.roster:
            print(p.name, "-", p.position, "-", p.proTeam)

#Player Info
print("\nPlayer Information:")

for t in league.teams:
    if t.team_id == 44:
        for p in t.roster:
            print(f"Name: {p.name}")
            print(f"Player ID: {p.playerId}")
            print(f"Position: {p.position}")
            print(f"NFL Team: {p.proTeam}")
            print(f"Injury Status: {p.injuryStatus}")
            print(f"Percent Owned: {p.percent_owned}")
            print(f"Percent Started: {p.percent_started}")
            print(f"Total Points: {p.total_points}")
            print(f"Average Points: {p.avg_points}")
            print(f"Projected Total Points: {p.projected_total_points}")
            print(f"Projected Average Points: {p.projected_avg_points}")
            print()

#Current Waiver Wire
print("\nWaiver Wire:")
for p in league.free_agents():
    print(p.name, "-", p.position, "-", p.proTeam)


# Weekly Player Stats
print("\nWeekly Player Stats:")

for team in league.teams:

    if team.team_id == 44:

        for player in team.roster:

            print(f"\nPlayer: {player.name}")
            print(f"Player ID: {player.playerId}")
            print(f"Position: {player.position}")
            print(f"NFL Team: {player.proTeam}")

            for week, stats in player.stats.items():

                # Skip season totals
                if week == 0:
                    continue

                # Skips future weeks that doesn't have data
                if "breakdown" not in stats:
                    continue

                breakdown = stats["breakdown"]

                print(f"\nWeek: {week}")
                print(f"Fantasy Points: {stats.get('points', 0)}")

                print(f"Rushing Attempts: {breakdown.get('rushingAttempts', 0)}")
                print(f"Rushing Yards: {breakdown.get('rushingYards', 0)}")
                print(f"Rushing Touchdowns: {breakdown.get('rushingTouchdowns', 0)}")
                print(f"Rushing 2PT Conversions: {breakdown.get('rushing2PtConversions', 0)}")

                print(f"Receiving Targets: {breakdown.get('receivingTargets', 0)}")
                print(f"Receiving Receptions: {breakdown.get('receivingReceptions', 0)}")
                print(f"Receiving Yards: {breakdown.get('receivingYards', 0)}")
                print(f"Receiving Touchdowns: {breakdown.get('receivingTouchdowns', 0)}")
                print(f"Receiving 2PT Conversions: {breakdown.get('receiving2PtConversions', 0)}")
                print(f"Receiving Yards After Catch: {breakdown.get('receivingYardsAfterCatch', 0)}")
                print(f"Receiving Yards Per Reception: {breakdown.get('receivingYardsPerReception', 0)}")

                print(f"Fumbles: {breakdown.get('fumbles', 0)}")
                print(f"Lost Fumbles: {breakdown.get('lostFumbles', 0)}")

