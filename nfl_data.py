import pandas as pd
import nflreadpy as nfl
from db import get_conn, load_df

SEASON = 2026
PRIOR_SEASON = 2025
WEEK = 3      # the week you're setting lineups for
K = 4         # how many "games" of last season's data to blend in

# Different sources spell some teams differently; normalize everything to one form
NORMALIZE = {"WSH": "WAS", "LAR": "LA", "JAC": "JAX", "OAK": "LV", "SD": "LAC", "STL": "LA"}
def norm(t):
    return NORMALIZE.get(t, t) if isinstance(t, str) else t


def load_weekly(seasons):
    df = nfl.load_player_stats(seasons).to_pandas()
    if "recent_team" in df.columns and "team" not in df.columns:
        df = df.rename(columns={"recent_team": "team"})
    if "season_type" in df.columns:
        df = df[df.season_type == "REG"]
    df["team"] = df.team.map(norm)
    df["opponent_team"] = df.opponent_team.map(norm)
    return df


def summarize(per_game):
    return per_game.groupby("opponent_team").agg(
        games=("week", "nunique"), carries=("carries", "sum"),
        rush_yds=("rush_yds", "sum"), targets=("targets", "sum"),
        rec_yds=("rec_yds", "sum"), fp=("fp", "sum"))


def defense_vs_pos(df, pos):
    d = df[df.position == pos]
    per_game = (d.groupby(["season", "opponent_team", "week"], as_index=False)
                  .agg(carries=("carries", "sum"), rush_yds=("rushing_yards", "sum"),
                       targets=("targets", "sum"), rec_yds=("receiving_yards", "sum"),
                       fp=("fantasy_points_ppr", "sum")))
    cur = summarize(per_game[per_game.season == SEASON])
    pri = summarize(per_game[per_game.season == PRIOR_SEASON])
    pri_pg = pri.drop(columns="games").div(pri.games, axis=0)   # last season, per game
    cur = cur.reindex(pri.index).fillna(0)

    # Blend this season with last season so 2 games of data don't swing everything
    out = pd.DataFrame({"games": cur.games})
    for c in ["carries", "targets", "rec_yds", "fp"]:
        out[f"{c}_pg"] = (cur[c] + K * pri_pg[c]) / (cur.games + K)
    out["ypc_allowed"] = (cur.rush_yds + K * pri_pg.rush_yds) / (cur.carries + K * pri_pg.carries)
    out["pos"] = pos
    out.index.name = "defense"
    return out.reset_index()


if __name__ == "__main__":
    conn = get_conn()

    df = load_weekly([PRIOR_SEASON, SEASON])
    print("Weeks loaded this season:", sorted(df[df.season == SEASON].week.unique()))

    # 1. Defense vs position
    dvp = pd.concat([defense_vs_pos(df, p) for p in ["RB", "WR", "TE"]])
    load_df(conn, dvp, "defense_vs_pos")

    # 2. Weekly usage for every RB/WR/TE (rostered or not), with team shares
    cur = df[df.season == SEASON].copy()
    team_tot = (cur.groupby(["team", "week"], as_index=False)
                   .agg(team_carries=("carries", "sum"), team_targets=("targets", "sum")))
    cur = cur.merge(team_tot, on=["team", "week"])
    cur["carry_share"] = cur.carries / cur.team_carries
    cur["target_share"] = cur.targets / cur.team_targets
    cols = ["player_id", "player_display_name", "position", "team", "opponent_team", "week",
            "carries", "carry_share", "targets", "target_share", "receptions",
            "rushing_yards", "rushing_tds", "receiving_yards", "receiving_tds",
            "fantasy_points_ppr"]
    usage = (cur[cur.position.isin(["RB", "WR", "TE"])][[c for c in cols if c in cur.columns]]
                .rename(columns={"player_id": "gsis_id"}))

    # 3. ID crosswalk so nflverse players can be matched to ESPN players
    ids = nfl.load_ff_playerids().to_pandas()[["gsis_id", "espn_id", "name", "position", "team"]]
    ids["espn_id"] = pd.to_numeric(ids.espn_id, errors="coerce")
    ids = ids.dropna(subset=["gsis_id", "espn_id"])
    ids["espn_id"] = ids.espn_id.astype("int64")
    load_df(conn, ids, "id_map")

    usage = usage.merge(ids[["gsis_id", "espn_id"]], on="gsis_id", how="left")
    load_df(conn, usage, "nfl_usage")

    # 4. This week's opponents from the NFL schedule
    sch = nfl.load_schedules([SEASON]).to_pandas()
    g = sch[sch.week == WEEK]
    matchups = pd.concat([
        pd.DataFrame({"team": g.home_team, "opponent": g.away_team, "home": True}),
        pd.DataFrame({"team": g.away_team, "opponent": g.home_team, "home": False}),
    ])
    matchups["team"] = matchups.team.map(norm)
    matchups["opponent"] = matchups.opponent.map(norm)
    matchups["week"] = WEEK
    load_df(conn, matchups, "matchups")

    conn.close()
    print("\nDone.")