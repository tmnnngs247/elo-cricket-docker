"""
Entry point for the Dockerized Elo pipeline.

    synthetic sample data (data/sample_*.csv)
                |
                v
        Elo rating engine (src/elo.py)
                |
                v
        outputs/elo_results.csv

Generates the sample data on the fly if it isn't already present, so
`docker run` works out of the box with no manual setup step.
"""

import subprocess
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from elo import build_elo_match_coupled  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
OUTPUT_PATH = ROOT / "outputs" / "elo_results.csv"

BAT_PATH = DATA_DIR / "sample_bat.csv"
BOWL_PATH = DATA_DIR / "sample_bowl.csv"


def ensure_sample_data():
    if BAT_PATH.exists() and BOWL_PATH.exists():
        return
    print("Sample data not found — generating synthetic dataset...")
    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "generate_sample_data.py")],
        check=True,
    )


def main():
    ensure_sample_data()

    print("Loading sample cricket data...")
    bat_df = pd.read_csv(BAT_PATH)
    bowl_df = pd.read_csv(BOWL_PATH)

    print(f"  batting rows: {len(bat_df)} | bowling rows: {len(bowl_df)}")
    print("Calculating Elo ratings (career-gated, opponent-adjusted, season-regressed)...")

    elo_df = build_elo_match_coupled(bat_df, bowl_df)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    elo_df.to_csv(OUTPUT_PATH, index=False)

    latest = (
        elo_df.sort_values("date")
        .groupby(["player_id", "role"], as_index=False)
        .last()[["player_id", "player_name", "role", "elo_post"]]
        .sort_values("elo_post", ascending=False)
    )

    print(f"\nFinished. {len(elo_df)} Elo update rows written to {OUTPUT_PATH}")
    print("\nTop 5 current ratings:")
    print(latest.head(5).to_string(index=False))


if __name__ == "__main__":
    main()
