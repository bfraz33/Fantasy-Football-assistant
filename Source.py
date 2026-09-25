import json
import pandas as pd
from espn_api.football import League
from db import get_conn, load_df

#Loading parameter credentials
def load_config(path="config/parameters.json"):
    with open(path) as f:
        return json.load(f)


def get_league(params):
    return League(league_id=params["league_id"], year=params["year"],
                  espn_s2=params["espn_s2"], swid=params["swid"])

#Pull team data based on team_id
def get_my_team(league, team_id):
    return next(t for t in league.teams if t.team_id == team_id)

#Players information on team
def player_row(p):
    return {
        "player_id": p.playerId, "name": p.name, "position": p.position,
        "nfl_team": p.proTeam, "injury_status": p.injuryStatus,
        "pct_owned": p.percent_owned, "pct_started": p.percent_started,
        "total_points": p.total_points, "avg_points": p.avg_points,
        "proj_total": p.projected_total_points, "proj_avg": p.projected_avg_points,
    }

#Weekly stats for players on team
def weekly_stat_rows(players):
    rows = []
    for p in players:
        for week, s in p.stats.items():
            if week == 0 or "breakdown" not in s:  # skip season totals & future weeks
                continue
            b = s["breakdown"]
            rows.append({
                "player_id": p.playerId, "name": p.name, "week": week,
                "fantasy_points": s.get("points", 0),
                "rush_att": b.get("rushingAttempts", 0),
                "rush_yds": b.get("rushingYards", 0),
                "rush_td": b.get("rushingTouchdowns", 0),
                "targets": b.get("receivingTargets", 0),
                "receptions": b.get("receivingReceptions", 0),
                "rec_yds": b.get("receivingYards", 0),
                "rec_td": b.get("receivingTouchdowns", 0),
                "fumbles_lost": b.get("lostFumbles", 0),
            })
    return rows

def season_total_rows(players):
    rows = []
    for p in players:
        s = p.stats.get(0)
        if not s or "breakdown" not in s:
            continue
        b = s["breakdown"]
        rows.append({
            "player_id": p.playerId, "name": p.name,
            "fantasy_points": s.get("points", 0),
            "rush_att": b.get("rushingAttempts", 0),
            "rush_yds": b.get("rushingYards", 0),
            "targets": b.get("receivingTargets", 0),
            "receptions": b.get("receivingReceptions", 0),
            "rec_yds": b.get("receivingYards", 0),
        })
    return rows


def projection_rows(players, week):
    rows = []
    for p in players:
        s = p.stats.get(week)
        if not s or "projected_breakdown" not in s:
            continue
        b = s["projected_breakdown"]
        rows.append({
            "player_id": p.playerId, "name": p.name, "week": week,
            "proj_points": s.get("projected_points", 0),
            "proj_rush_att": b.get("rushingAttempts", 0),
            "proj_rush_yds": b.get("rushingYards", 0),
            "proj_targets": b.get("receivingTargets", 0),
            "proj_receptions": b.get("receivingReceptions", 0),
            "proj_rec_yds": b.get("receivingYards", 0),
        })
    return rows

if __name__ == "__main__":
    params = load_config()
    league = get_league(params)
    print("Connected to league", params["league_id"], "for", params["year"])

    # Getting team roster and free agents, saving players to csv
    my_team = get_my_team(league, params["team_id"])
    roster = my_team.roster
    free_agents = league.free_agents(size=100)
    print(len(roster), "rostered,", len(free_agents), "free agents")

    # Creating dataframes for players and W stats
    players_df = pd.DataFrame([player_row(p) for p in roster + free_agents])
    stats_df = pd.DataFrame(weekly_stat_rows(roster + free_agents))

    # Diplaying data
    print("\nMy roster:")
    print(pd.DataFrame([player_row(p) for p in roster])
            [["name", "position", "nfl_team", "injury_status", "proj_avg"]]
            .to_string(index=False))

    print("\nWeekly stat rows:", len(stats_df))
    print(stats_df.head(10).to_string(index=False))

    all_players = roster + free_agents
    totals_df = pd.DataFrame(season_total_rows(all_players))
    proj_df = pd.DataFrame(projection_rows(all_players, league.current_week))

    print("\nSeason totals rows:", len(totals_df))
    print("Projection rows:", len(proj_df))
    print(proj_df[proj_df.name.isin(["Travis Etienne Jr.", "J.K. Dobbins", "Braelon Allen"])]
            .to_string(index=False))

    # Loading data to Snowflake
    conn = get_conn()
    load_df(conn, players_df, "players")
    load_df(conn, stats_df, "player_stats")
    load_df(conn, totals_df, "season_totals")



    proj_df["pulled_at"] = pd.Timestamp.now(tz="UTC").tz_localize(None)
    load_df(conn, proj_df, "projections", mode="append")   # keep every snapshot
    conn.close()

