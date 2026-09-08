"""
Plot Elo trajectories from a completed run, for the README.

Usage:
    python src/run_model.py            # produces outputs/elo_results.csv
    python scripts/plot_sample_elo.py  # produces docs/sample_elo_trajectories.png
"""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RESULTS_PATH = ROOT / "outputs" / "elo_results.csv"
OUT_PATH = ROOT / "docs" / "sample_elo_trajectories.png"

N_PLAYERS = 6


def main():
    if not RESULTS_PATH.exists():
        raise SystemExit(f"{RESULTS_PATH} not found — run `python src/run_model.py` first.")

    df = pd.read_csv(RESULTS_PATH, parse_dates=["date"])
    bat = df[df["role"] == "bat"].copy()

    top_players = (
        bat.sort_values("date")
        .groupby("player_id")["elo_post"]
        .last()
        .sort_values(ascending=False)
        .head(N_PLAYERS)
        .index
    )

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(8, 4.5))

    for pid in top_players:
        g = bat[bat["player_id"] == pid].sort_values("date")
        ax.plot(g["date"], g["elo_post"], marker="o", markersize=2, linewidth=1.3, label=g["player_name"].iloc[-1])

    ax.axhline(1500, color="grey", linewidth=0.8, linestyle="--", label="Starting Elo (1500)")
    ax.set_title("Batting Elo — top players, synthetic sample data")
    ax.set_xlabel("Match date")
    ax.set_ylabel("Elo rating")
    ax.legend(fontsize=8, loc="best")
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(OUT_PATH, dpi=150)
    print(f"Wrote {OUT_PATH}")


if __name__ == "__main__":
    main()
