from __future__ import annotations

import os
from pathlib import Path


EXPERIMENT_ROOT = Path(__file__).resolve().parent
REPO_ROOT = EXPERIMENT_ROOT.parent

# Input and outputs are project-owned by default.
PROCESSED_DIR = EXPERIMENT_ROOT / "data" / "processed"
INPUT_PROCESSED_DIR = Path(os.environ.get("ICU_MORTALITY_INPUT_DIR", PROCESSED_DIR))
TABLES_DIR = EXPERIMENT_ROOT / "outputs" / "tables"
FIGURES_DIR = EXPERIMENT_ROOT / "outputs" / "figures"
LOGS_DIR = EXPERIMENT_ROOT / "outputs" / "logs"
DOCS_DIR = EXPERIMENT_ROOT / "outputs" / "docs"

CH3_DATASET_NAME = "ch3_analysis_dataset.parquet"

TEST_SIZE = 0.2
RANDOM_STATE = 42
CV_FOLDS = 5
BOOTSTRAP_ROUNDS = 1000

TASK_NAME = "icu_28d_mortality"
DATASET_NAME = "icu_28d_mortality_dataset.parquet"
TARGET = "death_28d"

MIN_ICU_LOS_HOURS = 24.0

NUMERIC_FEATURES = [
    "anchor_age",
    "hr_first", "hr_mean", "hr_max",
    "rr_first", "rr_mean", "rr_max",
    "spo2_first", "spo2_mean", "spo2_min",
    "sbp_first", "sbp_mean", "sbp_min",
    "dbp_first", "dbp_mean", "dbp_min",
    "map_first", "map_mean", "map_min",
    "temp_first", "temp_mean", "temp_min", "temp_max",
    "wbc_first", "wbc_mean", "wbc_max",
    "hgb_first", "hgb_mean", "hgb_min", "hgb_max",
    "platelets_first", "platelets_mean", "platelets_min", "platelets_max",
    "na_first", "na_mean", "na_min", "na_max",
    "k_first", "k_mean", "k_min", "k_max",
    "cl_first", "cl_mean", "cl_min", "cl_max",
    "hco3_first", "hco3_mean", "hco3_min", "hco3_max",
    "creatinine_first", "creatinine_mean", "creatinine_max",
    "bun_first", "bun_mean", "bun_max",
    "glucose_first", "glucose_mean", "glucose_max",
    "anion_gap_first", "anion_gap_mean", "anion_gap_min", "anion_gap_max",
    "inr_first", "inr_mean", "inr_min", "inr_max",
    "ptt_first", "ptt_mean", "ptt_min", "ptt_max",
]

CATEGORICAL_FEATURES = [
    "gender",
    "race_group",
    "first_careunit",
]


def ensure_directories() -> None:
    for path in [PROCESSED_DIR, TABLES_DIR, FIGURES_DIR, LOGS_DIR, DOCS_DIR]:
        path.mkdir(parents=True, exist_ok=True)
