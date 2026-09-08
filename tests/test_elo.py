"""
Smoke tests for the Elo engine and synthetic sample-data generator.

These deliberately don't assert exact rating values (the algorithm has
randomness in the fixture data and is expected to evolve) — they check the
invariants that must always hold: the pipeline runs, ratings stay finite
and sane, the career-balls gate actually gates, and the sample generator
produces the schema the engine requires.
"""

import numpy as np
import pandas as pd
import pytest

from scripts.generate_sample_data import generate_sample_frames
from src.elo import build_elo_match_coupled


@pytest.fixture(scope="module")
def sample_frames():
    # Small, fast fixture — a handful of teams/players/seasons is enough to
    # exercise every branch (gating, season regression, opponent lookup).
    return generate_sample_frames(seed=1, n_seasons=2, n_teams=3, n_players_per_team=6, matches_per_pair=1)


@pytest.fixture(scope="module")
def elo_result(sample_frames):
    bat_df, bowl_df = sample_frames
    return build_elo_match_coupled(bat_df, bowl_df, min_career_balls=12)


def test_generate_sample_frames_schema(sample_frames):
    bat_df, bowl_df = sample_frames

    required_bat_cols = {
        "match_id", "start_date", "season", "player_id", "player_name",
        "team_id", "opposition_team_id", "batting_order_position",
        "runs", "balls_faced", "delivery_over_no",
    }
    required_bowl_cols = {
        "match_id", "start_date", "player_id", "player_name",
        "team_id", "opposition_team_id", "runs", "balls", "delivery_over_no",
    }

    assert required_bat_cols.issubset(bat_df.columns)
    assert required_bowl_cols.issubset(bowl_df.columns)
    assert len(bat_df) > 0
    assert len(bowl_df) > 0


def test_generate_sample_frames_is_deterministic():
    a_bat, a_bowl = generate_sample_frames(seed=7, n_seasons=1, n_teams=2, n_players_per_team=4, matches_per_pair=1)
    b_bat, b_bowl = generate_sample_frames(seed=7, n_seasons=1, n_teams=2, n_players_per_team=4, matches_per_pair=1)

    pd.testing.assert_frame_equal(a_bat, b_bat)
    pd.testing.assert_frame_equal(a_bowl, b_bowl)


def test_elo_output_schema_and_roles(elo_result):
    expected_cols = {
        "date", "season", "match_id", "player_id", "player_name", "role",
        "balls", "runs", "elo_pre", "elo_post", "delta",
    }
    assert expected_cols.issubset(elo_result.columns)
    assert set(elo_result["role"].unique()) <= {"bat", "bowl"}
    assert len(elo_result) > 0


def test_elo_ratings_are_finite(elo_result):
    assert np.isfinite(elo_result["elo_pre"]).all()
    assert np.isfinite(elo_result["elo_post"]).all()
    assert np.isfinite(elo_result["delta"]).all()


def test_career_gate_freezes_early_ratings(elo_result):
    """Before a player has faced/bowled `min_career_balls`, their rating
    must not move (delta stays 0 and elo_post == elo_pre)."""
    gated = elo_result[elo_result["cum_balls_after"] <= 12]
    if gated.empty:
        pytest.skip("no rows below the gate threshold in this fixture")
    assert (gated["delta"] == 0.0).all()
    assert np.allclose(gated["elo_pre"], gated["elo_post"])


def test_elo_deltas_are_bounded(elo_result):
    max_delta = 35.0  # default max_delta in build_elo_match_coupled
    assert (elo_result["delta"].abs() <= max_delta + 1e-9).all()


def test_ratings_start_near_1500(elo_result):
    # First appearance for every player should start from (or very close
    # to) the 1500 baseline, since nothing has adjusted them yet.
    first_rows = elo_result.sort_values("date").groupby(["player_id", "role"]).first()
    assert first_rows["elo_pre"].between(1490, 1510).all()
