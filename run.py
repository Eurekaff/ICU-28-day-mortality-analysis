from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from prolonged_icu_los_experiment.build_dataset import build_dataset
    from prolonged_icu_los_experiment.settings import ensure_directories
    from prolonged_icu_los_experiment.train_eval import train_and_evaluate
else:
    from .build_dataset import build_dataset
    from .settings import ensure_directories
    from .train_eval import train_and_evaluate


def main() -> None:
    parser = argparse.ArgumentParser(description="Run prolonged ICU LOS prediction module.")
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
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
    os.environ.setdefault("MPLBACKEND", "Agg")
    ensure_directories()

    if args.build_only and args.train_only:
        raise ValueError("--build-only and --train-only cannot be used together.")

    if not args.train_only:
        build_dataset()

    if not args.build_only:
        kwargs = {"model_names": args.models}
        if args.bootstrap_rounds is not None:
            kwargs["bootstrap_rounds"] = args.bootstrap_rounds
        train_and_evaluate(**kwargs)


if __name__ == "__main__":
    main()
