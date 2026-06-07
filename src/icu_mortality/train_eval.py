from __future__ import annotations

import logging
from typing import Iterable

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.calibration import calibration_curve
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    brier_score_loss,
    confusion_matrix,
    f1_score,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)
from sklearn.model_selection import GridSearchCV, StratifiedKFold, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

try:
    from .io_utils import load_df, save_df
    from .model_specs import get_model_specs
    from .config import (
        BOOTSTRAP_ROUNDS,
        CATEGORICAL_FEATURES,
        CV_FOLDS,
        DATASET_NAME,
        FIGURES_DIR,
        NUMERIC_FEATURES,
        PROCESSED_DIR,
        RANDOM_STATE,
        SHAP_SAMPLE_SIZE,
        TABLES_DIR,
        TASK_NAME,
        TARGET,
        TEST_SIZE,
    )
except ImportError:
    from io_utils import load_df, save_df
    from model_specs import get_model_specs
    from config import (
        BOOTSTRAP_ROUNDS,
        CATEGORICAL_FEATURES,
        CV_FOLDS,
        DATASET_NAME,
        FIGURES_DIR,
        NUMERIC_FEATURES,
        PROCESSED_DIR,
        RANDOM_STATE,
        SHAP_SAMPLE_SIZE,
        TABLES_DIR,
        TASK_NAME,
        TARGET,
        TEST_SIZE,
    )

logger = logging.getLogger(__name__)


def build_preprocessor(numeric_features: list[str], categorical_features: list[str]) -> ColumnTransformer:
    numeric_pipe = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
    ])
    categorical_pipe = Pipeline([
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("onehot", OneHotEncoder(handle_unknown="ignore")),
    ])
    return ColumnTransformer(
        transformers=[
            ("num", numeric_pipe, numeric_features),
            ("cat", categorical_pipe, categorical_features),
        ],
        remainder="drop",
        sparse_threshold=0.0,
    )


def make_baseline_table(
    df: pd.DataFrame,
    numeric_features: list[str],
    categorical_features: list[str],
) -> pd.DataFrame:
    rows = []
    non_event = df.loc[df[TARGET] == 0].copy()
    event = df.loc[df[TARGET] == 1].copy()

    for col in numeric_features:
        a = pd.to_numeric(non_event[col], errors="coerce").dropna()
        b = pd.to_numeric(event[col], errors="coerce").dropna()
        rows.append({
            "variable": col,
            "level": "",
            "survivor_group": f"{a.mean():.2f} +/- {a.std(ddof=1):.2f}" if len(a) else "NA",
            "death_28d_group": f"{b.mean():.2f} +/- {b.std(ddof=1):.2f}" if len(b) else "NA",
        })

    for col in categorical_features:
        levels = sorted(df[col].astype("object").fillna("Missing").unique().tolist())
        for idx, level in enumerate(levels):
            a = non_event[col].astype("object").fillna("Missing")
            b = event[col].astype("object").fillna("Missing")
            a_n = int((a == level).sum())
            b_n = int((b == level).sum())
            rows.append({
                "variable": col if idx == 0 else "",
                "level": level,
                "survivor_group": f"{a_n} ({100 * a_n / len(a):.2f}%)" if len(a) else "NA",
                "death_28d_group": f"{b_n} ({100 * b_n / len(b):.2f}%)" if len(b) else "NA",
            })

    return pd.DataFrame(rows)


def get_best_f1_threshold(y_true: np.ndarray, y_prob: np.ndarray) -> float:
    precision, recall, thresholds = precision_recall_curve(y_true, y_prob)
    if len(thresholds) == 0:
        return 0.5
    f1_scores = []
    for p, r in zip(precision[:-1], recall[:-1]):
        denom = p + r
        f1_scores.append(0.0 if denom == 0 else 2 * p * r / denom)
    return float(thresholds[int(np.argmax(f1_scores))])


def evaluate_predictions(y_true: np.ndarray, y_prob: np.ndarray, threshold: float) -> dict:
    y_pred = (y_prob >= threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
    return {
        "auroc": roc_auc_score(y_true, y_prob),
        "auprc": average_precision_score(y_true, y_prob),
        "accuracy": accuracy_score(y_true, y_pred),
        "precision": precision_score(y_true, y_pred, zero_division=0),
        "recall": recall_score(y_true, y_pred, zero_division=0),
        "f1": f1_score(y_true, y_pred, zero_division=0),
        "brier": brier_score_loss(y_true, y_prob),
        "tn": int(tn),
        "fp": int(fp),
        "fn": int(fn),
        "tp": int(tp),
    }


def bootstrap_ci(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    threshold: float,
    n_bootstrap: int,
    random_state: int,
) -> pd.DataFrame:
    if n_bootstrap <= 0:
        return pd.DataFrame()

    rng = np.random.default_rng(random_state)
    rows = []
    n = len(y_true)
    for _ in range(n_bootstrap):
        idx = rng.integers(0, n, n)
        yt = y_true[idx]
        yp = y_prob[idx]
        if len(np.unique(yt)) < 2:
            continue
        rows.append(evaluate_predictions(yt, yp, threshold))

    boot = pd.DataFrame(rows)
    out_rows = []
    for metric in ["auroc", "auprc", "accuracy", "precision", "recall", "f1", "brier"]:
        out_rows.append({
            "metric": metric,
            "mean": boot[metric].mean(),
            "lcl_95": boot[metric].quantile(0.025),
            "ucl_95": boot[metric].quantile(0.975),
        })
    return pd.DataFrame(out_rows)


def plot_roc(curves: dict[str, tuple[np.ndarray, np.ndarray, float]]) -> None:
    plt.figure(figsize=(7, 6))
    for name, (fpr, tpr, auc_val) in curves.items():
        plt.plot(fpr, tpr, label=f"{name} (AUC={auc_val:.3f})")
    plt.plot([0, 1], [0, 1], linestyle="--")
    plt.xlabel("False Positive Rate")
    plt.ylabel("True Positive Rate")
    plt.legend()
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / f"{TASK_NAME}_roc.png", dpi=300)
    plt.close()


def plot_pr(curves: dict[str, tuple[np.ndarray, np.ndarray, float]]) -> None:
    plt.figure(figsize=(7, 6))
    for name, (recall, precision, ap_val) in curves.items():
        plt.plot(recall, precision, label=f"{name} (AUPRC={ap_val:.3f})")
    plt.xlabel("Recall")
    plt.ylabel("Precision")
    plt.legend()
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / f"{TASK_NAME}_pr.png", dpi=300)
    plt.close()


def plot_calibration(y_true: np.ndarray, y_prob: np.ndarray, model_name: str) -> None:
    plt.figure(figsize=(7, 6))
    frac_pos, mean_pred = calibration_curve(y_true, y_prob, n_bins=5, strategy="quantile")
    plt.plot(mean_pred, frac_pos, marker="s", label=model_name)
    plt.plot([0, 1], [0, 1], linestyle=":", color="black", label="Perfectly calibrated")
    plt.xlabel("Mean predicted probability")
    plt.ylabel("Fraction of positives")
    plt.legend()
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / f"{TASK_NAME}_calibration.png", dpi=300)
    plt.close()


def save_feature_importance(best_pipeline: Pipeline) -> None:
    model = best_pipeline.named_steps["model"]
    preprocessor = best_pipeline.named_steps["preprocess"]
    feature_names = preprocessor.get_feature_names_out()

    values = None
    importance_type = ""
    if hasattr(model, "feature_importances_"):
        values = model.feature_importances_
        importance_type = "feature_importances"
    elif hasattr(model, "coef_"):
        values = np.ravel(np.abs(model.coef_))
        importance_type = "absolute_coefficient"

    if values is None:
        logger.info("Best model does not expose feature importance or coefficients; skipping importance table.")
        return

    out = (
        pd.DataFrame({
            "feature": feature_names,
            "importance": values,
            "importance_type": importance_type,
        })
        .sort_values("importance", ascending=False)
        .reset_index(drop=True)
    )
    save_df(out, TABLES_DIR / f"{TASK_NAME}_feature_importance.csv")


def _as_dense_array(values):
    if hasattr(values, "toarray"):
        return values.toarray()
    return np.asarray(values)


def _positive_class_shap_values(shap_values):
    if isinstance(shap_values, list):
        return shap_values[1] if len(shap_values) > 1 else shap_values[0]
    arr = np.asarray(shap_values)
    if arr.ndim == 3:
        return arr[:, :, 1] if arr.shape[2] > 1 else arr[:, :, 0]
    return arr


def _display_feature_name(name: str) -> str:
    if name.startswith("num__"):
        return name.removeprefix("num__")
    if name.startswith("cat__"):
        display = name.removeprefix("cat__")
        replacements = {
            "first_careunit_Cardiac Vascular Intensive Care Unit (CVICU)": "first_careunit_CVICU",
            "first_careunit_Coronary Care Unit (CCU)": "first_careunit_CCU",
            "first_careunit_Medical Intensive Care Unit (MICU)": "first_careunit_MICU",
            "first_careunit_Medical/Surgical Intensive Care Unit (MICU/SICU)": "first_careunit_MICU/SICU",
            "first_careunit_Neuro Intermediate": "first_careunit_Neuro Intermediate",
            "first_careunit_Neuro Surgical Intensive Care Unit (Neuro SICU)": "first_careunit_Neuro SICU",
            "first_careunit_Surgical Intensive Care Unit (SICU)": "first_careunit_SICU",
            "first_careunit_Trauma SICU (TSICU)": "first_careunit_TSICU",
        }
        return replacements.get(display, display)
    return name


def save_shap_explanations(
    best_pipeline: Pipeline,
    x_test: pd.DataFrame,
    model_name: str,
    sample_size: int = SHAP_SAMPLE_SIZE,
    random_state: int = RANDOM_STATE,
) -> None:
    try:
        import shap
    except ImportError:
        logger.warning("Skipping SHAP explanations because the 'shap' package is unavailable.")
        return

    if sample_size <= 0:
        logger.info("Skipping SHAP explanations because sample_size <= 0.")
        return

    preprocessor = best_pipeline.named_steps["preprocess"]
    model = best_pipeline.named_steps["model"]
    feature_names = preprocessor.get_feature_names_out()
    x_transformed = preprocessor.transform(x_test)

    rng = np.random.default_rng(random_state)
    n_rows = x_transformed.shape[0]
    sample_n = min(sample_size, n_rows)
    sample_idx = np.sort(rng.choice(n_rows, size=sample_n, replace=False))
    x_sample = _as_dense_array(x_transformed[sample_idx])
    x_sample_df = pd.DataFrame(x_sample, columns=feature_names)

    try:
        explainer = shap.TreeExplainer(model)
        shap_values = _positive_class_shap_values(explainer.shap_values(x_sample_df))
    except Exception as exc:
        logger.warning("Skipping SHAP explanations for %s because TreeExplainer failed: %s", model_name, exc)
        return

    mean_abs = np.abs(shap_values).mean(axis=0)
    importance_df = (
        pd.DataFrame({
            "feature": feature_names,
            "display_feature": [_display_feature_name(name) for name in feature_names],
            "mean_abs_shap": mean_abs,
            "model": model_name,
            "n_explained": sample_n,
        })
        .sort_values("mean_abs_shap", ascending=False)
        .reset_index(drop=True)
    )
    save_df(importance_df, TABLES_DIR / f"{TASK_NAME}_shap_importance.csv")

    top_plot = importance_df.head(10).iloc[::-1]
    plt.figure(figsize=(8, 4.4))
    plt.barh(top_plot["display_feature"], top_plot["mean_abs_shap"], color="#4c78a8")
    plt.xlabel("Mean absolute SHAP value")
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / f"{TASK_NAME}_shap_importance_bar.png", dpi=300, bbox_inches="tight")
    plt.close()

    with plt.rc_context({"font.size": 9, "axes.titlesize": 13, "axes.labelsize": 10}):
        shap.summary_plot(
            shap_values,
            x_sample_df.rename(columns=_display_feature_name),
            max_display=12,
            show=False,
            plot_size=(10, 6),
        )
        plt.title(f"{model_name} SHAP summary")
        plt.tight_layout()
    plt.savefig(FIGURES_DIR / f"{TASK_NAME}_shap_summary.png", dpi=300, bbox_inches="tight")
    plt.close()


def _selected_specs(model_names: Iterable[str] | None):
    specs = get_model_specs()
    if model_names is None:
        return specs
    requested = set(model_names)
    return [spec for spec in specs if spec.name in requested]


def train_and_evaluate(
    model_names: Iterable[str] | None = None,
    bootstrap_rounds: int = BOOTSTRAP_ROUNDS,
) -> pd.DataFrame:
    dataset_path = PROCESSED_DIR / DATASET_NAME
    if not dataset_path.exists() and not dataset_path.with_suffix(".csv").exists():
        raise FileNotFoundError(f"Missing {TASK_NAME} dataset. Run the build step first.")

    df = load_df(dataset_path if dataset_path.exists() else dataset_path.with_suffix(".csv")).copy()
    numeric_features = [c for c in NUMERIC_FEATURES if c in df.columns]
    categorical_features = [c for c in CATEGORICAL_FEATURES if c in df.columns]

    y = df[TARGET].astype(int).values
    if len(np.unique(y)) < 2:
        raise ValueError("Target has only one class.")

    baseline_df = make_baseline_table(df, numeric_features, categorical_features)
    save_df(baseline_df, TABLES_DIR / f"{TASK_NAME}_table1_baseline_by_outcome.csv")

    x = df[numeric_features + categorical_features].copy()
    x_train, x_test, y_train, y_test = train_test_split(
        x,
        y,
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE,
        stratify=y,
    )

    min_class_count = int(np.bincount(y_train).min())
    n_splits = min(CV_FOLDS, min_class_count)
    if n_splits < 2:
        raise ValueError("Not enough samples in each class for stratified cross-validation.")

    preprocessor = build_preprocessor(numeric_features, categorical_features)
    cv = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=RANDOM_STATE)

    perf_rows = []
    threshold_rows = []
    confusion_rows = []
    roc_curves = {}
    pr_curves = {}
    best_model_name = None
    best_model_auroc = -np.inf
    best_pipeline = None
    best_y_prob_test = None
    best_y_prob_train = None

    specs = _selected_specs(model_names)
    if not specs:
        raise ValueError("No available model specs matched the requested model names.")

    logger.info("Training models: %s", ", ".join(spec.name for spec in specs))

    for spec in specs:
        logger.info("Training %s", spec.name)
        pipe = Pipeline([
            ("preprocess", clone(preprocessor)),
            ("model", clone(spec.estimator)),
        ])
        search = GridSearchCV(
            estimator=pipe,
            param_grid=spec.param_grid,
            scoring="roc_auc",
            cv=cv,
            n_jobs=1,
            refit=True,
        )
        try:
            search.fit(x_train, y_train)
        except Exception as exc:
            logger.warning("Skipping %s because training failed: %s", spec.name, exc)
            continue

        best_pipe = search.best_estimator_
        y_prob_train = best_pipe.predict_proba(x_train)[:, 1]
        y_prob_test = best_pipe.predict_proba(x_test)[:, 1]
        threshold = get_best_f1_threshold(y_train, y_prob_train)
        metrics = evaluate_predictions(y_test, y_prob_test, threshold)

        perf_rows.append({
            "model": spec.name,
            "best_params": str(search.best_params_),
            "cv_best_roc_auc": search.best_score_,
            "test_auroc": metrics["auroc"],
            "test_auprc": metrics["auprc"],
            "test_accuracy": metrics["accuracy"],
            "test_precision": metrics["precision"],
            "test_recall": metrics["recall"],
            "test_f1": metrics["f1"],
            "test_brier": metrics["brier"],
        })
        threshold_rows.append({
            "model": spec.name,
            "best_f1_threshold": threshold,
            "test_accuracy": metrics["accuracy"],
            "test_precision": metrics["precision"],
            "test_recall": metrics["recall"],
            "test_f1": metrics["f1"],
        })
        confusion_rows.append({
            "model": spec.name,
            "threshold": threshold,
            "tn": metrics["tn"],
            "fp": metrics["fp"],
            "fn": metrics["fn"],
            "tp": metrics["tp"],
        })

        fpr, tpr, _ = roc_curve(y_test, y_prob_test)
        roc_curves[spec.name] = (fpr, tpr, metrics["auroc"])
        precision, recall, _ = precision_recall_curve(y_test, y_prob_test)
        pr_curves[spec.name] = (recall, precision, metrics["auprc"])

        if metrics["auroc"] > best_model_auroc:
            best_model_auroc = metrics["auroc"]
            best_model_name = spec.name
            best_pipeline = best_pipe
            best_y_prob_test = y_prob_test
            best_y_prob_train = y_prob_train

    if not perf_rows or best_pipeline is None:
        raise RuntimeError("All model training attempts failed.")

    perf_df = pd.DataFrame(perf_rows).sort_values("test_auroc", ascending=False).reset_index(drop=True)
    threshold_df = pd.DataFrame(threshold_rows).sort_values("model").reset_index(drop=True)
    confusion_df = pd.DataFrame(confusion_rows).sort_values("model").reset_index(drop=True)

    save_df(perf_df, TABLES_DIR / f"{TASK_NAME}_table2_model_performance.csv")
    save_df(threshold_df, TABLES_DIR / f"{TASK_NAME}_table3_best_threshold_metrics.csv")
    save_df(confusion_df, TABLES_DIR / f"{TASK_NAME}_confusion_matrix.csv")

    plot_roc(roc_curves)
    plot_pr(pr_curves)
    plot_calibration(y_test, best_y_prob_test, best_model_name)
    save_feature_importance(best_pipeline)
    save_shap_explanations(best_pipeline, x_test, best_model_name)

    best_threshold = get_best_f1_threshold(y_train, best_y_prob_train)
    boot_df = bootstrap_ci(
        y_true=y_test,
        y_prob=best_y_prob_test,
        threshold=best_threshold,
        n_bootstrap=bootstrap_rounds,
        random_state=RANDOM_STATE,
    )
    if not boot_df.empty:
        save_df(boot_df, TABLES_DIR / f"{TASK_NAME}_table4_best_model_bootstrap_ci.csv")

    pred_df = df.loc[x_test.index, ["subject_id", "hadm_id", "stay_id", "icu_los_days"]].copy()
    pred_df["y_true"] = y_test
    pred_df["y_prob"] = best_y_prob_test
    save_df(pred_df, PROCESSED_DIR / f"{TASK_NAME}_best_model_test_predictions.csv")

    joblib.dump(best_pipeline, PROCESSED_DIR / f"{TASK_NAME}_best_model.joblib")

    meta_df = pd.DataFrame([{
        "best_model": best_model_name,
        "best_model_test_auroc": best_model_auroc,
        "n_train": len(x_train),
        "n_test": len(x_test),
        "n_train_events": int(y_train.sum()),
        "n_test_events": int(y_test.sum()),
        "n_cv_folds": n_splits,
    }])
    save_df(meta_df, PROCESSED_DIR / f"{TASK_NAME}_best_model_meta.csv")

    logger.info("Saved %s performance tables, figures, predictions, and best model.", TASK_NAME)
    logger.info("Best model: %s, test AUROC: %.4f", best_model_name, best_model_auroc)

    return perf_df
