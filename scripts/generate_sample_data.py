"""
Generate a small synthetic List A cricket dataset matching the schema the
Elo engine (src/elo.py) expects, so the pipeline can be built, run, and
demonstrated in Docker without any real ECB data or database credentials.

Usage:
    python scripts/generate_sample_data.py

Writes:
    data/sample_bat.csv
    data/sample_bowl.csv
"""

from pathlib import Path

import numpy as np
import pandas as pd

SEED = 42
N_SEASONS = 3
N_TEAMS = 4
N_PLAYERS_PER_TEAM = 8
MATCHES_PER_SEASON_PER_TEAM_PAIR = 2

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def main():
    rng = np.random.default_rng(SEED)

    teams = [f"Team {chr(65 + i)}" for i in range(N_TEAMS)]  # Team A..D
    team_ids = {t: i + 1 for i, t in enumerate(teams)}

    # Each team gets a fixed squad of batter/bowler-capable player ids.
    players = {}
    pid = 1
    for team in teams:
        squad = []
        for _ in range(N_PLAYERS_PER_TEAM):
            squad.append({"player_id": pid, "player_name": f"Player {pid:03d}", "team": team})
            pid += 1
        players[team] = squad

    bat_rows = []
    bowl_rows = []
    match_id = 1

    for season_offset in range(N_SEASONS):
        season = 2022 + season_offset
        season_start = pd.Timestamp(f"{season}-05-01")

        for i, team_a in enumerate(teams):
            for team_b in teams[i + 1:]:
                for game in range(MATCHES_PER_SEASON_PER_TEAM_PAIR):
                    match_date = season_start + pd.Timedelta(days=int(rng.integers(0, 120)))
                    home, away = (team_a, team_b) if game % 2 == 0 else (team_b, team_a)

                    for batting_team, bowling_team in [(home, away), (away, home)]:
                        batters = players[batting_team]
                        bowlers = players[bowling_team]

                        for order, batter in enumerate(batters, start=1):
                            balls_faced = int(rng.integers(0, 70))
                            if balls_faced == 0:
                                runs = 0
                            else:
                                runs = int(max(0, rng.normal(loc=balls_faced * 0.85, scale=balls_faced * 0.35)))
                            delivery_over_no = int(rng.integers(1, 50))

                            bat_rows.append({
                                "match_id": match_id,
                                "start_date": match_date.date().isoformat(),
                                "season": season,
                                "player_id": batter["player_id"],
                                "player_name": batter["player_name"],
                                "team_id": team_ids[batting_team],
                                "team_name": batting_team,
                                "opposition_team_id": team_ids[bowling_team],
                                "opposition_team": bowling_team,
                                "batting_order_position": order,
                                "runs": runs,
                                "balls_faced": balls_faced,
                                "delivery_over_no": delivery_over_no,
                            })

                        # A handful of the batting team's bowlers bowl at the other side.
                        for bowler in bowlers[:5]:
                            balls = int(rng.integers(0, 60))
                            if balls == 0:
                                runs = 0
                            else:
                                runs = int(max(0, rng.normal(loc=balls * 0.8, scale=balls * 0.3)))
                            delivery_over_no = int(rng.integers(1, 50))

                            bowl_rows.append({
                                "match_id": match_id,
                                "start_date": match_date.date().isoformat(),
                                "player_id": bowler["player_id"],
                                "player_name": bowler["player_name"],
                                "team_id": team_ids[bowling_team],
                                "team_name": bowling_team,
                                "opposition_team_id": team_ids[batting_team],
                                "opposition_team": batting_team,
                                "runs": runs,
                                "balls": balls,
                                "delivery_over_no": delivery_over_no,
                            })

                    match_id += 1

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    bat_df = pd.DataFrame(bat_rows)
    bowl_df = pd.DataFrame(bowl_rows)
    bat_df.to_csv(DATA_DIR / "sample_bat.csv", index=False)
    bowl_df.to_csv(DATA_DIR / "sample_bowl.csv", index=False)

    print(f"Wrote {len(bat_df)} batting rows and {len(bowl_df)} bowling rows across {match_id - 1} synthetic matches.")
    print(f"  -> {DATA_DIR / 'sample_bat.csv'}")
    print(f"  -> {DATA_DIR / 'sample_bowl.csv'}")


if __name__ == "__main__":
    main()
