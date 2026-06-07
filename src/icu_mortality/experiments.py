from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Iterable

import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.calibration import CalibratedClassifierCV
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import GridSearchCV, StratifiedKFold, train_test_split
from sklearn.pipeline import Pipeline

try:
    from .config import (
        CATEGORICAL_FEATURES,
        CV_FOLDS,
        DATASET_NAME,
        NUMERIC_FEATURES,
        PROCESSED_DIR,
        RANDOM_STATE,
        TABLES_DIR,
        TASK_NAME,
        TARGET,
        TEST_SIZE,
    )
    from .io_utils import load_df, save_df
    from .model_specs import ModelSpec, get_model_specs
    from .train_eval import (
        _as_dense_array,
        _display_feature_name,
        _positive_class_shap_values,
        build_preprocessor,
        evaluate_predictions,
        get_best_f1_threshold,
    )
except ImportError:
    from config import (  # type: ignore
        CATEGORICAL_FEATURES,
        CV_FOLDS,
        DATASET_NAME,
        NUMERIC_FEATURES,
        PROCESSED_DIR,
        RANDOM_STATE,
        TABLES_DIR,
        TASK_NAME,
        TARGET,
        TEST_SIZE,
    )
    from io_utils import load_df, save_df  # type: ignore
    from model_specs import ModelSpec, get_model_specs  # type: ignore
    from train_eval import (  # type: ignore
        _as_dense_array,
        _display_feature_name,
        _positive_class_shap_values,
        build_preprocessor,
        evaluate_predictions,
        get_best_f1_threshold,
    )


logger = logging.getLogger(__name__)

VITAL_PREFIXES = ("hr_", "rr_", "spo2_", "sbp_", "dbp_", "map_", "temp_")
LAB_PREFIXES = (
    "wbc_",
    "hgb_",
    "platelets_",
    "na_",
    "k_",
    "cl_",
    "hco3_",
    "creatinine_",
    "bun_",
    "glucose_",
    "anion_gap_",
    "inr_",
    "ptt_",
)
DEMOGRAPHIC_COLUMNS = ("anchor_age", "gender", "race_group", "first_careunit")


@dataclass
class SplitData:
    x_train: pd.DataFrame
    x_test: pd.DataFrame
    y_train: np.ndarray
    y_test: np.ndarray


@dataclass
class FitResult:
    model: str
    pipeline: Pipeline
    y_prob_train: np.ndarray
    y_prob_test: np.ndarray
    threshold: float
    cv_best_roc_auc: float
    best_params: dict
    metrics: dict


def _available(columns: Iterable[str], df: pd.DataFrame) -> list[str]:
    return [col for col in columns if col in df.columns]


def feature_groups(
    df: pd.DataFrame,
    numeric_features: list[str],
    categorical_features: list[str],
) -> dict[str, list[str]]:
    numeric = _available(numeric_features, df)
    categorical = _available(categorical_features, df)
    demographics = _available(DEMOGRAPHIC_COLUMNS, df)
    vitals = [col for col in numeric if col.startswith(VITAL_PREFIXES)]
    labs = [col for col in numeric if col.startswith(LAB_PREFIXES)]
    first_only = [col for col in numeric if col.endswith("_first")] + categorical
    summary = [
        col
        for col in numeric
        if col.endswith(("_mean", "_min", "_max"))
    ] + categorical
    return {
        "demographics": demographics,
        "vitals": vitals,
        "labs": labs,
        "first_only": first_only,
        "summary_only": summary,
        "full": numeric + categorical,
    }


def grouped_numeric_features(numeric_features: list[str]) -> dict[str, list[str]]:
    return {
        "vitals": [col for col in numeric_features if col.startswith(VITAL_PREFIXES)],
        "labs": [col for col in numeric_features if col.startswith(LAB_PREFIXES)],
        "renal": [col for col in numeric_features if col.startswith(("creatinine_", "bun_"))],
        "coagulation": [col for col in numeric_features if col.startswith(("inr_", "ptt_"))],
        "electrolytes": [
            col
            for col in numeric_features
            if col.startswith(("na_", "k_", "cl_", "hco3_", "anion_gap_"))
        ],
    }


def add_missingness_features(
    df: pd.DataFrame,
    numeric_features: list[str],
    groups: dict[str, list[str]],
) -> tuple[pd.DataFrame, list[str]]:
    out = df.copy()
    numeric_out = list(numeric_features)
    for col in numeric_features:
        if col not in out.columns:
            continue
        new_col = f"{col}_is_missing"
        out[new_col] = out[col].isna().astype(int)
        numeric_out.append(new_col)

    for group_name, cols in groups.items():
        available_cols = [col for col in cols if col in out.columns]
        if not available_cols:
            continue
        new_col = f"missing_burden_{group_name}"
        out[new_col] = out[available_cols].isna().mean(axis=1).astype(float)
        numeric_out.append(new_col)

    return out, numeric_out


def calibration_summary(y_true: np.ndarray, y_prob: np.ndarray) -> dict:
    y_prob = np.clip(np.asarray(y_prob, dtype=float), 1e-6, 1 - 1e-6)
    y_true = np.asarray(y_true, dtype=int)
    logits = np.log(y_prob / (1 - y_prob)).reshape(-1, 1)
    if len(np.unique(y_true)) < 2:
        slope = np.nan
        intercept = np.nan
    else:
        cal_model = LogisticRegression(solver="lbfgs")
        cal_model.fit(logits, y_true)
        slope = float(cal_model.coef_[0][0])
        intercept = float(cal_model.intercept_[0])
    return {
        "brier": float(np.mean((y_prob - y_true) ** 2)),
        "calibration_slope": slope,
        "calibration_intercept": intercept,
    }


def risk_bin_table(y_true: np.ndarray, y_prob: np.ndarray, n_bins: int = 5) -> pd.DataFrame:
    df = pd.DataFrame({"y_true": y_true, "y_prob": y_prob}).sort_values("y_prob").reset_index(drop=True)
    bins = min(n_bins, len(df))
    df["risk_bin"] = pd.qcut(df.index, q=bins, labels=[f"Q{i}" for i in range(1, bins + 1)])
    grouped = df.groupby("risk_bin", observed=True)
    return grouped.agg(
        n=("y_true", "size"),
        observed_event_rate=("y_true", "mean"),
        mean_predicted_risk=("y_prob", "mean"),
        min_predicted_risk=("y_prob", "min"),
        max_predicted_risk=("y_prob", "max"),
    ).reset_index()


def _selected_specs(model_names: Iterable[str] | None) -> list[ModelSpec]:
    specs = get_model_specs()
    if model_names is None:
        preferred = {"HistGradientBoosting", "XGBoost", "LightGBM"}
        selected = [spec for spec in specs if spec.name in preferred]
        return selected or specs[:3]
    requested = set(model_names)
    return [spec for spec in specs if spec.name in requested]


def _split_xy(df: pd.DataFrame, features: list[str]) -> SplitData:
    x = df[features].copy()
    y = df[TARGET].astype(int).values
    x_train, x_test, y_train, y_test = train_test_split(
        x,
        y,
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE,
        stratify=y,
    )
    return SplitData(x_train=x_train, x_test=x_test, y_train=y_train, y_test=y_test)


def _cv_for(y_train: np.ndarray) -> StratifiedKFold:
    min_class_count = int(np.bincount(y_train).min())
    n_splits = min(CV_FOLDS, min_class_count)
    if n_splits < 2:
        raise ValueError("Not enough samples in each class for stratified cross-validation.")
    return StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=RANDOM_STATE)


def train_single_model(
    df: pd.DataFrame,
    spec: ModelSpec,
    numeric_features: list[str],
    categorical_features: list[str],
    tune: bool = False,
) -> FitResult:
    features = numeric_features + categorical_features
    split = _split_xy(df, features)
    preprocessor = build_preprocessor(numeric_features, categorical_features)
    pipe = Pipeline([
        ("preprocess", preprocessor),
        ("model", clone(spec.estimator)),
    ])
    if tune:
        search = GridSearchCV(
            estimator=pipe,
            param_grid=spec.param_grid,
            scoring="roc_auc",
            cv=_cv_for(split.y_train),
            n_jobs=1,
            refit=True,
        )
        search.fit(split.x_train, split.y_train)
        best_pipe = search.best_estimator_
        cv_best_roc_auc = float(search.best_score_)
        best_params = search.best_params_
    else:
        best_pipe = pipe.fit(split.x_train, split.y_train)
        cv_best_roc_auc = float("nan")
        best_params = {}
    y_prob_train = best_pipe.predict_proba(split.x_train)[:, 1]
    y_prob_test = best_pipe.predict_proba(split.x_test)[:, 1]
    threshold = get_best_f1_threshold(split.y_train, y_prob_train)
    metrics = evaluate_predictions(split.y_test, y_prob_test, threshold)
    return FitResult(
        model=spec.name,
        pipeline=best_pipe,
        y_prob_train=y_prob_train,
        y_prob_test=y_prob_test,
        threshold=threshold,
        cv_best_roc_auc=cv_best_roc_auc,
        best_params=best_params,
        metrics=metrics,
    )


def _performance_row(experiment: str, fit: FitResult, extra: dict | None = None) -> dict:
    row = {
        "experiment": experiment,
        "model": fit.model,
        "best_params": str(fit.best_params),
        "cv_best_roc_auc": fit.cv_best_roc_auc,
        "threshold": fit.threshold,
        "test_auroc": fit.metrics["auroc"],
        "test_auprc": fit.metrics["auprc"],
        "test_accuracy": fit.metrics["accuracy"],
        "test_precision": fit.metrics["precision"],
        "test_recall": fit.metrics["recall"],
        "test_f1": fit.metrics["f1"],
        "test_brier": fit.metrics["brier"],
    }
    if extra:
        row.update(extra)
    return row


def run_ablation_experiments(
    df: pd.DataFrame,
    model_names: Iterable[str] | None,
    max_groups: Iterable[str] | None = None,
) -> pd.DataFrame:
    numeric_features = _available(NUMERIC_FEATURES, df)
    categorical_features = _available(CATEGORICAL_FEATURES, df)
    groups = feature_groups(df, numeric_features, categorical_features)
    selected_groups = list(max_groups) if max_groups is not None else [
        "demographics",
        "vitals",
        "labs",
        "first_only",
        "summary_only",
        "full",
    ]
    specs = _selected_specs(model_names)
    rows = []
    for group_name in selected_groups:
        features = groups.get(group_name, [])
        if not features:
            continue
        numeric_group = [col for col in features if col in numeric_features]
        categorical_group = [col for col in features if col in categorical_features]
        for spec in specs:
            logger.info("Ablation %s / %s", group_name, spec.name)
            try:
                fit = train_single_model(df, spec, numeric_group, categorical_group)
            except Exception as exc:
                logger.warning("Skipping ablation %s / %s: %s", group_name, spec.name, exc)
                continue
            rows.append(_performance_row(group_name, fit, {"n_features": len(features)}))
    out = pd.DataFrame(rows)
    if not out.empty:
        save_df(out, TABLES_DIR / f"{TASK_NAME}_ablation_performance.csv")
    return out


def run_missingness_experiments(
    df: pd.DataFrame,
    model_names: Iterable[str] | None,
) -> pd.DataFrame:
    numeric_features = _available(NUMERIC_FEATURES, df)
    categorical_features = _available(CATEGORICAL_FEATURES, df)
    groups = grouped_numeric_features(numeric_features)
    specs = _selected_specs(model_names)
    rows = []

    for spec in specs:
        logger.info("Missingness base / %s", spec.name)
        fit = train_single_model(df, spec, numeric_features, categorical_features)
        rows.append(_performance_row("base_imputation", fit, {"n_features": len(numeric_features + categorical_features)}))

    miss_df, miss_numeric = add_missingness_features(df, numeric_features, groups)
    for spec in specs:
        logger.info("Missingness indicators / %s", spec.name)
        fit = train_single_model(miss_df, spec, miss_numeric, categorical_features)
        rows.append(_performance_row("missing_indicators_and_burden", fit, {"n_features": len(miss_numeric + categorical_features)}))

    out = pd.DataFrame(rows)
    if not out.empty:
        save_df(out, TABLES_DIR / f"{TASK_NAME}_missingness_performance.csv")
    return out


def run_calibration_experiments(
    df: pd.DataFrame,
    model_names: Iterable[str] | None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    numeric_features = _available(NUMERIC_FEATURES, df)
    categorical_features = _available(CATEGORICAL_FEATURES, df)
    features = numeric_features + categorical_features
    split = _split_xy(df, features)
    specs = _selected_specs(model_names)
    rows = []
    risk_rows = []
    for spec in specs:
        logger.info("Calibration / %s", spec.name)
        base_fit = train_single_model(df, spec, numeric_features, categorical_features)
        for method_name, calibrated in [
            ("uncalibrated", base_fit.pipeline),
            (
                "sigmoid",
                CalibratedClassifierCV(estimator=clone(base_fit.pipeline), method="sigmoid", cv=3),
            ),
            (
                "isotonic",
                CalibratedClassifierCV(estimator=clone(base_fit.pipeline), method="isotonic", cv=3),
            ),
        ]:
            if method_name == "uncalibrated":
                y_prob_train = base_fit.y_prob_train
                y_prob = base_fit.y_prob_test
            else:
                calibrated.fit(split.x_train, split.y_train)
                y_prob_train = calibrated.predict_proba(split.x_train)[:, 1]
                y_prob = calibrated.predict_proba(split.x_test)[:, 1]
            threshold = get_best_f1_threshold(split.y_train, y_prob_train)
            metrics = evaluate_predictions(split.y_test, y_prob, threshold)
            cal = calibration_summary(split.y_test, y_prob)
            rows.append({
                "model": spec.name,
                "calibration": method_name,
                "test_auroc": metrics["auroc"],
                "test_auprc": metrics["auprc"],
                "test_brier": metrics["brier"],
                "calibration_slope": cal["calibration_slope"],
                "calibration_intercept": cal["calibration_intercept"],
                "threshold": threshold,
                "test_precision": metrics["precision"],
                "test_recall": metrics["recall"],
                "test_f1": metrics["f1"],
            })
            bins = risk_bin_table(split.y_test, y_prob, n_bins=5)
            bins.insert(0, "calibration", method_name)
            bins.insert(0, "model", spec.name)
            risk_rows.extend(bins.to_dict("records"))

    cal_df = pd.DataFrame(rows)
    risk_df = pd.DataFrame(risk_rows)
    if not cal_df.empty:
        save_df(cal_df, TABLES_DIR / f"{TASK_NAME}_calibration_comparison.csv")
    if not risk_df.empty:
        save_df(risk_df, TABLES_DIR / f"{TASK_NAME}_risk_bins.csv")
    return cal_df, risk_df


def run_shap_stability_experiments(
    df: pd.DataFrame,
    model_names: Iterable[str] | None,
    sample_size: int = 500,
    repeats: int = 5,
) -> pd.DataFrame:
    try:
        import shap
    except ImportError:
        logger.warning("Skipping SHAP stability because shap is unavailable.")
        return pd.DataFrame()

    numeric_features = _available(NUMERIC_FEATURES, df)
    categorical_features = _available(CATEGORICAL_FEATURES, df)
    specs = _selected_specs(model_names)
    rows = []
    rng = np.random.default_rng(RANDOM_STATE)
    for spec in specs:
        logger.info("SHAP stability / %s", spec.name)
        try:
            fit = train_single_model(df, spec, numeric_features, categorical_features)
        except Exception as exc:
            logger.warning("Skipping SHAP stability for %s: %s", spec.name, exc)
            continue
        model = fit.pipeline.named_steps["model"]
        if not hasattr(model, "feature_importances_"):
            logger.info("Skipping SHAP stability for %s because it is not a tree model.", spec.name)
            continue
        preprocessor = fit.pipeline.named_steps["preprocess"]
        feature_names = preprocessor.get_feature_names_out()
        x_all = df[numeric_features + categorical_features].copy()
        transformed = preprocessor.transform(x_all)
        n_rows = transformed.shape[0]
        explain_n = min(sample_size, n_rows)
        top_counts: dict[str, int] = {}
        for repeat_idx in range(repeats):
            idx = np.sort(rng.choice(n_rows, size=explain_n, replace=False))
            x_sample = _as_dense_array(transformed[idx])
            x_sample_df = pd.DataFrame(x_sample, columns=feature_names)
            try:
                explainer = shap.TreeExplainer(model)
                shap_values = _positive_class_shap_values(explainer.shap_values(x_sample_df))
            except Exception as exc:
                logger.warning("Skipping SHAP repeat %s for %s: %s", repeat_idx, spec.name, exc)
                continue
            mean_abs = np.abs(shap_values).mean(axis=0)
            top_idx = np.argsort(mean_abs)[::-1][:10]
            for feature in [_display_feature_name(feature_names[i]) for i in top_idx]:
                top_counts[feature] = top_counts.get(feature, 0) + 1
        for feature, count in sorted(top_counts.items(), key=lambda item: (-item[1], item[0])):
            rows.append({
                "model": spec.name,
                "display_feature": feature,
                "top10_count": count,
                "n_repeats": repeats,
                "stability_rate": count / repeats,
                "sample_size": explain_n,
            })
    out = pd.DataFrame(rows)
    if not out.empty:
        save_df(out, TABLES_DIR / f"{TASK_NAME}_shap_stability.csv")
    return out


def run_extended_experiments(
    model_names: Iterable[str] | None = None,
    shap_sample_size: int = 500,
    shap_repeats: int = 5,
) -> dict[str, pd.DataFrame]:
    dataset_path = PROCESSED_DIR / DATASET_NAME
    if not dataset_path.exists() and not dataset_path.with_suffix(".csv").exists():
        raise FileNotFoundError(f"Missing {TASK_NAME} dataset. Run the build step first.")
    df = load_df(dataset_path if dataset_path.exists() else dataset_path.with_suffix(".csv")).copy()
    outputs: dict[str, pd.DataFrame] = {}
    outputs["ablation"] = run_ablation_experiments(df, model_names)
    outputs["missingness"] = run_missingness_experiments(df, model_names)
    cal_df, risk_df = run_calibration_experiments(df, model_names)
    outputs["calibration"] = cal_df
    outputs["risk_bins"] = risk_df
    outputs["shap_stability"] = run_shap_stability_experiments(
        df,
        model_names,
        sample_size=shap_sample_size,
        repeats=shap_repeats,
    )
    return outputs
