# Cricket Elo Rating Engine

![Docker](https://img.shields.io/badge/docker-ready-2496ED?logo=docker&logoColor=white)
![Python](https://img.shields.io/badge/python-3.12-blue?logo=python&logoColor=white)
![Build](https://github.com/tmnnngs247/elo-cricket-docker/actions/workflows/docker-build.yml/badge.svg)

A match-coupled, career-gated Elo rating engine for List A / ODI cricket, built
as the statistical core of an MSc dissertation on Elo-based talent
identification — used to test whether a player's rating at the point of
selection predicts whether they get picked for England.

Ratings are:

- built separately for batting and bowling,
- opponent-adjusted (weighted against the average current Elo of the
  bowlers/batters actually faced that match),
- season-regressed toward the starting rating at each player's first
  appearance in a new season,
- gated so a player's rating doesn't move until they've faced/bowled a
  minimum number of career balls, and
- updated with a dynamic K-factor based on balls faced/bowled, match
  experience, and recent-form volatility.

This repository packages that engine as a **reproducible, containerised
pipeline** — clone it, `docker run`, get Elo ratings out, no setup required:

```text
Synthetic match data (data/sample_*.csv)
              │
              ▼
   Elo rating engine (src/elo.py)
              │
              ▼
  outputs/elo_results.csv
```

It deliberately containerises the **computational pipeline**, not the
original data source. The full dissertation work runs against a private
ECB data lake; that connection code, and the real dataset, are **not** part
of this repo or image. Instead, the Docker image runs against a small
synthetic dataset with the same schema, so anyone can clone this repo and
reproduce a working Elo pipeline without database access or credentials of
any kind.

## Example output

Batting Elo trajectories for the top 6 players in one run of the synthetic
sample dataset (regenerate with `python src/run_model.py && python
scripts/plot_sample_elo.py`):

![Sample Elo trajectories](docs/sample_elo_trajectories.png)

## Project layout

```
elo-cricket-docker/
├── src/
│   ├── elo.py                  # Elo engine — takes bat/bowl DataFrames, source-agnostic
│   └── run_model.py            # entry point: load data -> calculate Elo -> write output
├── scripts/
│   ├── generate_sample_data.py # builds a small synthetic dataset matching the schema
│   └── plot_sample_elo.py      # renders docs/sample_elo_trajectories.png from a run
├── tests/
│   └── test_elo.py             # pytest smoke tests for the engine + sample-data generator
├── docs/
│   └── sample_elo_trajectories.png
├── data/                        # sample_bat.csv / sample_bowl.csv (generated, gitignored)
├── outputs/                     # elo_results.csv (generated, gitignored)
├── requirements.txt
├── requirements-dev.txt        # pytest, for running the test suite
├── Dockerfile
├── .dockerignore
└── .github/workflows/docker-build.yml   # CI: pytest, then docker build + smoke run
```

## Running locally (no Docker)

```bash
pip install -r requirements.txt
python scripts/generate_sample_data.py   # optional — run_model.py will do this automatically
python src/run_model.py
```

## Running with Docker

### Build

```bash
docker build -t cricket-elo .
```

### Run

```bash
docker run --rm cricket-elo
```

### Run and keep the output on your machine

```bash
docker run --rm -v "$(pwd)/outputs:/app/outputs" cricket-elo
```

`outputs/elo_results.csv` will then appear in this repo on the host.

## Tests

A small pytest suite checks the Elo engine and sample-data generator behave
correctly (gating, finite ratings, expected schema). CI runs this on every
push, then builds the Docker image and does a smoke-test `docker run`.

```bash
pip install -r requirements.txt -r requirements-dev.txt
pytest
```

## Notes on the real (non-Docker) pipeline

The dissertation notebooks that load real ECB data and run the full
selection-hypothesis pipeline (H1/H2/H3) live outside this repo and
connect to a private database over credentials that must **never** be
committed to source control. This container intentionally has no
database connectivity — it exists to demonstrate that the modelling
code itself is packaged, reproducible, and independently runnable.
