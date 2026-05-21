from __future__ import annotations

import logging

import pandas as pd

from .io_utils import load_df, save_df
from .settings import (
    CATEGORICAL_FEATURES,
    CH3_DATASET_NAME,
    DATASET_NAME,
    INPUT_PROCESSED_DIR,
    LABEL_MODE,
    MIN_ICU_LOS_HOURS,
    NUMERIC_FEATURES,
    PROCESSED_DIR,
    TABLES_DIR,
    TARGET,
    THRESHOLD_DAYS,
)

logger = logging.getLogger(__name__)


def _load_processed_dataset(name: str) -> pd.DataFrame:
    path = INPUT_PROCESSED_DIR / name
    if path.exists():
        return load_df(path)

    csv_path = path.with_suffix(".csv")
    if csv_path.exists():
        return load_df(csv_path)

    raise FileNotFoundError(f"Missing {name}. Run stage1 and stage2 first.")


def get_los_threshold_days(los_days: pd.Series) -> tuple[float, str]:
    mode = LABEL_MODE.lower()

    if mode == "fixed_days":
        return float(THRESHOLD_DAYS), f"fixed_{THRESHOLD_DAYS:g}d"
    if mode == "median":
        return float(los_days.median()), "median"
    if mode == "q75":
        return float(los_days.quantile(0.75)), "q75"

    raise ValueError(f"Unsupported LABEL_MODE: {LABEL_MODE}")


def build_dataset() -> pd.DataFrame:
    df = _load_processed_dataset(CH3_DATASET_NAME).copy()

    df["icu_los_hours"] = pd.to_numeric(df["icu_los_hours"], errors="coerce")
    df["icu_los_days"] = df["icu_los_hours"] / 24.0

    cohort = df.loc[
        (df["ad_flag"] == 1)
        & df["icu_los_hours"].notna()
        & (df["icu_los_hours"] >= MIN_ICU_LOS_HOURS)
    ].copy()

    if cohort.empty:
        raise ValueError("No valid AD ICU cohort found for prolonged ICU LOS prediction.")

    threshold_days, threshold_name = get_los_threshold_days(cohort["icu_los_days"])
    cohort[TARGET] = (cohort["icu_los_days"] > threshold_days).astype(int)

    numeric_features = [c for c in NUMERIC_FEATURES if c in cohort.columns]
    categorical_features = [c for c in CATEGORICAL_FEATURES if c in cohort.columns]

    keep_cols = [
        "subject_id",
        "hadm_id",
        "stay_id",
        "icu_los_hours",
        "icu_los_days",
        TARGET,
    ] + numeric_features + categorical_features

    out = cohort[keep_cols].copy()

    for col in numeric_features:
        out[col] = pd.to_numeric(out[col], errors="coerce")
    for col in categorical_features:
        out[col] = out[col].astype("object")
    out[TARGET] = out[TARGET].astype(int)

    output_path = PROCESSED_DIR / DATASET_NAME
    save_df(out, output_path)

    summary = pd.DataFrame([{
        "task_name": "prolonged_icu_los",
        "label_mode": LABEL_MODE,
        "threshold_name": threshold_name,
        "threshold_days": threshold_days,
        "threshold_hours": threshold_days * 24.0,
        "n_total": len(out),
        "n_events": int(out[TARGET].sum()),
        "event_rate": float(out[TARGET].mean()),
        "n_numeric_features": len(numeric_features),
        "n_categorical_features": len(categorical_features),
    }])
    save_df(summary, TABLES_DIR / "prolonged_icu_los_dataset_summary.csv")

    missing = (
        out.isna().mean()
        .sort_values(ascending=False)
        .rename("missing_rate")
        .rename_axis("variable")
        .reset_index()
    )
    save_df(missing, TABLES_DIR / "prolonged_icu_los_missing_summary.csv")

    logger.info("Saved dataset: %s", output_path)
    logger.info("Threshold: %s (%.2f days)", threshold_name, threshold_days)
    logger.info(
        "Cohort size: n=%s, events=%s, event_rate=%.4f",
        len(out),
        int(out[TARGET].sum()),
        float(out[TARGET].mean()),
    )

    return out


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
    build_dataset()
