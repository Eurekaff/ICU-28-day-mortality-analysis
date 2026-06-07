from __future__ import annotations

from dataclasses import dataclass
import importlib
import logging

from sklearn.ensemble import ExtraTreesClassifier, HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier

try:
    from .config import RANDOM_STATE
except ImportError:
    from config import RANDOM_STATE


logger = logging.getLogger(__name__)


@dataclass
class ModelSpec:
    name: str
    estimator: object
    param_grid: dict


def _optional_classifier(module_name: str, class_name: str):
    try:
        module = importlib.import_module(module_name)
        return getattr(module, class_name)
    except Exception as exc:
        logger.warning(
            "Skipping %s because optional dependency '%s' is unavailable: %s",
            class_name,
            module_name,
            exc,
        )
        return None


def get_model_specs() -> list[ModelSpec]:
    specs = [
        ModelSpec(
            name="LogisticRegression",
            estimator=LogisticRegression(
                max_iter=5000,
                solver="lbfgs",
                class_weight="balanced",
                random_state=RANDOM_STATE,
            ),
            param_grid={"model__C": [0.1, 0.5, 1.0, 2.0]},
        ),
        ModelSpec(
            name="DecisionTree",
            estimator=DecisionTreeClassifier(class_weight="balanced", random_state=RANDOM_STATE),
            param_grid={"model__max_depth": [None, 3, 5], "model__min_samples_leaf": [1, 5, 10]},
        ),
        ModelSpec(
            name="RandomForest",
            estimator=RandomForestClassifier(class_weight="balanced", random_state=RANDOM_STATE, n_jobs=1),
            param_grid={
                "model__n_estimators": [100],
                "model__max_depth": [6],
                "model__min_samples_leaf": [5],
            },
        ),
        ModelSpec(
            name="ExtraTrees",
            estimator=ExtraTreesClassifier(class_weight="balanced", random_state=RANDOM_STATE, n_jobs=1),
            param_grid={
                "model__n_estimators": [100],
                "model__max_depth": [6],
                "model__min_samples_leaf": [5],
            },
        ),
        ModelSpec(
            name="HistGradientBoosting",
            estimator=HistGradientBoostingClassifier(random_state=RANDOM_STATE),
            param_grid={
                "model__learning_rate": [0.03, 0.05],
                "model__max_depth": [3, None],
                "model__max_iter": [200, 400],
            },
        ),
    ]

    XGBClassifier = _optional_classifier("xgboost", "XGBClassifier")
    if XGBClassifier is not None:
        specs.append(ModelSpec(
            name="XGBoost",
            estimator=XGBClassifier(
                objective="binary:logistic",
                eval_metric="logloss",
                random_state=RANDOM_STATE,
                n_jobs=1,
            ),
            param_grid={
                "model__n_estimators": [200, 400],
                "model__max_depth": [2, 3],
                "model__learning_rate": [0.03, 0.05],
            },
        ))

    LGBMClassifier = _optional_classifier("lightgbm", "LGBMClassifier")
    if LGBMClassifier is not None:
        specs.append(ModelSpec(
            name="LightGBM",
            estimator=LGBMClassifier(
                objective="binary",
                class_weight="balanced",
                random_state=RANDOM_STATE,
                n_jobs=1,
                verbosity=-1,
            ),
            param_grid={
                "model__n_estimators": [200, 400],
                "model__num_leaves": [15, 31],
                "model__learning_rate": [0.03, 0.05],
            },
        ))

    CatBoostClassifier = _optional_classifier("catboost", "CatBoostClassifier")
    if CatBoostClassifier is not None:
        specs.append(ModelSpec(
            name="CatBoost",
            estimator=CatBoostClassifier(
                loss_function="Logloss",
                eval_metric="AUC",
                auto_class_weights="Balanced",
                random_seed=RANDOM_STATE,
                verbose=False,
                allow_writing_files=False,
                thread_count=1,
            ),
            param_grid={"model__iterations": [200, 400], "model__depth": [3, 4], "model__learning_rate": [0.03, 0.05]},
        ))

    return specs
