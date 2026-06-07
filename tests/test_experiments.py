from __future__ import annotations

import sys
import os
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("MPLBACKEND", "Agg")
os.environ.setdefault("MPLCONFIGDIR", str(PROJECT_ROOT / ".matplotlib-cache"))
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from icu_mortality.experiments import (  # noqa: E402
    add_missingness_features,
    calibration_summary,
    feature_groups,
    risk_bin_table,
)


def test_feature_groups_use_available_columns_only():
    df = pd.DataFrame(
        {
            "anchor_age": [70, 80],
            "gender": ["M", "F"],
            "hr_first": [80, 95],
            "hr_mean": [85, 97],
            "bun_mean": [20, 44],
            "wbc_first": [8, 11],
            "first_careunit": ["MICU", "SICU"],
            "missing_config_feature": [1, 2],
        }
    )
    groups = feature_groups(
        df=df,
        numeric_features=[
            "anchor_age",
            "hr_first",
            "hr_mean",
            "bun_mean",
            "wbc_first",
            "not_present",
        ],
        categorical_features=["gender", "first_careunit", "not_present_cat"],
    )

    assert groups["demographics"] == ["anchor_age", "gender", "first_careunit"]
    assert groups["vitals"] == ["hr_first", "hr_mean"]
    assert groups["labs"] == ["bun_mean", "wbc_first"]
    assert groups["first_only"] == ["hr_first", "wbc_first", "gender", "first_careunit"]
    assert groups["full"] == [
        "anchor_age",
        "hr_first",
        "hr_mean",
        "bun_mean",
        "wbc_first",
        "gender",
        "first_careunit",
    ]


def test_add_missingness_features_adds_indicators_and_group_burden_without_mutation():
    df = pd.DataFrame(
        {
            "hr_first": [80.0, np.nan, 90.0],
            "bun_mean": [np.nan, 30.0, 40.0],
            "gender": ["M", "F", None],
        }
    )
    original = df.copy(deep=True)

    out, numeric_out = add_missingness_features(
        df=df,
        numeric_features=["hr_first", "bun_mean"],
        groups={"vitals": ["hr_first"], "labs": ["bun_mean"]},
    )

    pd.testing.assert_frame_equal(df, original)
    assert "hr_first_is_missing" in out.columns
    assert "bun_mean_is_missing" in out.columns
    assert "missing_burden_vitals" in out.columns
    assert "missing_burden_labs" in out.columns
    assert out["hr_first_is_missing"].tolist() == [0, 1, 0]
    assert out["bun_mean_is_missing"].tolist() == [1, 0, 0]
    assert out["missing_burden_vitals"].tolist() == [0.0, 1.0, 0.0]
    assert out["missing_burden_labs"].tolist() == [1.0, 0.0, 0.0]
    assert "hr_first_is_missing" in numeric_out
    assert "missing_burden_labs" in numeric_out


def test_calibration_summary_returns_brier_slope_and_intercept():
    y_true = np.array([0, 0, 1, 1])
    y_prob = np.array([0.1, 0.2, 0.8, 0.9])

    summary = calibration_summary(y_true, y_prob)

    assert summary["brier"] < 0.05
    assert summary["calibration_slope"] > 0
    assert np.isfinite(summary["calibration_intercept"])


def test_risk_bin_table_returns_quantile_bins_with_counts_and_event_rates():
    y_true = np.array([0, 0, 1, 0, 1, 1])
    y_prob = np.array([0.05, 0.15, 0.25, 0.65, 0.75, 0.95])

    table = risk_bin_table(y_true, y_prob, n_bins=3)

    assert table["risk_bin"].tolist() == ["Q1", "Q2", "Q3"]
    assert table["n"].tolist() == [2, 2, 2]
    assert table["observed_event_rate"].tolist() == [0.0, 0.5, 1.0]
    assert table["mean_predicted_risk"].is_monotonic_increasing
