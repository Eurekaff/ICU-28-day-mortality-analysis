from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
os.environ.setdefault("MPLBACKEND", "Agg")
os.environ.setdefault("MPLCONFIGDIR", str(PROJECT_ROOT / ".matplotlib-cache"))
os.environ.setdefault("LOKY_MAX_CPU_COUNT", "4")
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from icu_mortality.config import ensure_directories
from icu_mortality.dataset import build_dataset
from icu_mortality.experiments import run_extended_experiments
from icu_mortality.train_eval import train_and_evaluate


def main() -> None:
    parser = argparse.ArgumentParser(description="Run ICU 28-day mortality prediction module.")
    parser.add_argument("--build-only", action="store_true", help="Only build the modeling dataset.")
    parser.add_argument("--train-only", action="store_true", help="Only train/evaluate from an existing dataset.")
    parser.add_argument(
        "--models",
        nargs="+",
        default=None,
        help="Optional subset of model names, e.g. LogisticRegression DecisionTree.",
    )
    parser.add_argument(
        "--bootstrap-rounds",
        type=int,
        default=None,
        help="Override bootstrap rounds. Use 0 for a quick smoke test.",
    )
    parser.add_argument(
        "--extended-experiments",
        action="store_true",
        help="Run calibration, missingness, ablation, and SHAP stability experiments.",
    )
    parser.add_argument(
        "--extended-only",
        action="store_true",
        help="Run only redesigned extended experiments and skip baseline train/evaluate.",
    )
    parser.add_argument(
        "--extended-models",
        nargs="+",
        default=None,
        help="Optional model subset for extended experiments.",
    )
    parser.add_argument(
        "--shap-stability-sample-size",
        type=int,
        default=500,
        help="Rows per SHAP stability repeat.",
    )
    parser.add_argument(
        "--shap-stability-repeats",
        type=int,
        default=5,
        help="Number of SHAP stability repeats.",
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
    ensure_directories()

    if args.build_only and args.train_only:
        raise ValueError("--build-only and --train-only cannot be used together.")

    if not args.train_only:
        build_dataset()

    if args.extended_only and not args.extended_experiments:
        raise ValueError("--extended-only requires --extended-experiments.")

    if not args.build_only and not args.extended_only:
        kwargs = {"model_names": args.models}
        if args.bootstrap_rounds is not None:
            kwargs["bootstrap_rounds"] = args.bootstrap_rounds
        train_and_evaluate(**kwargs)

    if args.extended_experiments:
        run_extended_experiments(
            model_names=args.extended_models,
            shap_sample_size=args.shap_stability_sample_size,
            shap_repeats=args.shap_stability_repeats,
        )


if __name__ == "__main__":
    main()
