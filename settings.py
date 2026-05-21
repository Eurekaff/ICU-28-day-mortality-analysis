from __future__ import annotations

import os
from pathlib import Path


EXPERIMENT_ROOT = Path(__file__).resolve().parent
REPO_ROOT = EXPERIMENT_ROOT.parent

# Input and outputs are project-owned by default.
PROCESSED_DIR = EXPERIMENT_ROOT / "data" / "processed"
INPUT_PROCESSED_DIR = Path(os.environ.get("PROLONGED_ICU_LOS_INPUT_DIR", PROCESSED_DIR))
TABLES_DIR = EXPERIMENT_ROOT / "outputs" / "tables"
FIGURES_DIR = EXPERIMENT_ROOT / "outputs" / "figures"
LOGS_DIR = EXPERIMENT_ROOT / "outputs" / "logs"
DOCS_DIR = EXPERIMENT_ROOT / "outputs" / "docs"

CH3_DATASET_NAME = "ch3_analysis_dataset.parquet"

TEST_SIZE = 0.2
RANDOM_STATE = 42
CV_FOLDS = 5
BOOTSTRAP_ROUNDS = 1000

TASK_NAME = "prolonged_icu_los"
DATASET_NAME = "prolonged_icu_los_dataset.parquet"
TARGET = "prolonged_icu_los"

# Label modes: "fixed_days", "median", "q75".
LABEL_MODE = "fixed_days"
THRESHOLD_DAYS = 7.0
MIN_ICU_LOS_HOURS = 24.0

NUMERIC_FEATURES = [
    "anchor_age",
    "hr_first", "hr_mean", "hr_max",
    "rr_first", "rr_mean", "rr_max",
    "spo2_first", "spo2_mean", "spo2_min",
    "sbp_first", "sbp_mean", "sbp_min",
    "dbp_first", "dbp_mean", "dbp_min",
    "map_first", "map_mean", "map_min",
    "wbc_first", "wbc_mean", "wbc_max",
    "hgb_first",
    "platelets_first",
    "na_first",
    "k_first",
    "cl_first",
    "hco3_first",
    "creatinine_first", "creatinine_mean", "creatinine_max",
    "bun_first", "bun_mean", "bun_max",
    "glucose_first", "glucose_mean", "glucose_max",
    "anion_gap_first",
    "inr_first",
    "ptt_first",
    "lactate_first",
    "lactate_max",
    "bilirubin_first",
    "albumin_first",
    "gcs_total_first",
    "gcs_total_min",
]

CATEGORICAL_FEATURES = [
    "gender",
    "race_group",
    "first_careunit",
]


def ensure_directories() -> None:
    for path in [PROCESSED_DIR, TABLES_DIR, FIGURES_DIR, LOGS_DIR, DOCS_DIR]:
        path.mkdir(parents=True, exist_ok=True)
