# ICU Extended Experiments Implementation Plan

> **For agentic workers:** Use eureka-dev-playbook:subagent-driven-development for independent high-risk or broad tasks, or eureka-dev-playbook:executing-plans for inline execution. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement and run the redesigned ICU mortality experiments for missingness, feature ablation, calibration, and explanation stability while preserving the existing baseline workflow.

**Architecture:** Keep `train_eval.py` as the baseline trainer and add `src/icu_mortality/experiments.py` for extension experiments with small pure helpers that are unit-tested. Add a CLI flag in `run.py` so baseline and extended experiments can be run together or separately.

**Tech Stack:** Python, pandas, numpy, scikit-learn, matplotlib, existing `.venv`, pytest-style tests using stdlib assertions.

---

### Task 1: Add Experiment Helper Tests

**Files:**
- Create: `tests/test_experiments.py`

- [x] **Step 1: Write tests for feature group selection, missingness augmentation, calibration metrics, and risk bins**

Create tests that assert:
- `feature_groups()` returns demographics, vitals, labs, first-only, and full groups using only columns present in an input DataFrame.
- `add_missingness_features()` adds `_is_missing` numeric indicators and group burden columns without mutating the original DataFrame.
- `calibration_summary()` returns Brier score plus calibration slope/intercept for non-degenerate probabilities.
- `risk_bin_table()` returns monotonic quantile bins with observed event rates and row counts.

- [x] **Step 2: Verify tests fail before implementation**

Run:

```bash
.venv/bin/python tests/test_experiments.py
```

Expected: fail because `icu_mortality.experiments` is missing.

### Task 2: Implement Extended Experiment Module

**Files:**
- Create: `src/icu_mortality/experiments.py`

- [x] **Step 1: Implement pure helpers**

Implement:
- `feature_groups(df, numeric_features, categorical_features)`
- `add_missingness_features(df, numeric_features, groups)`
- `calibration_summary(y_true, y_prob)`
- `risk_bin_table(y_true, y_prob, n_bins=5)`

- [x] **Step 2: Implement model runner helpers**

Implement:
- `train_single_model(...)` using the existing `ModelSpec`, `build_preprocessor`, `get_best_f1_threshold`, and `evaluate_predictions`.
- `run_ablation_experiments(...)`
- `run_missingness_experiments(...)`
- `run_calibration_experiments(...)`
- `run_shap_stability_experiments(...)`
- `run_extended_experiments(...)`

Output tables:
- `outputs/tables/icu_28d_mortality_ablation_performance.csv`
- `outputs/tables/icu_28d_mortality_missingness_performance.csv`
- `outputs/tables/icu_28d_mortality_calibration_comparison.csv`
- `outputs/tables/icu_28d_mortality_risk_bins.csv`
- `outputs/tables/icu_28d_mortality_shap_stability.csv`

- [x] **Step 3: Verify helper tests pass**

Run:

```bash
.venv/bin/python tests/test_experiments.py
```

Expected: all tests pass.

### Task 3: Wire CLI

**Files:**
- Modify: `run.py`

- [x] **Step 1: Add CLI flags**

Add:
- `--extended-experiments` to run redesigned experiment modules.
- `--extended-models` to select models for extended experiments; default to `HistGradientBoosting`, `XGBoost`, and `LightGBM` when available.

- [x] **Step 2: Smoke test CLI**

Run:

```bash
.venv/bin/python run.py --train-only --models LogisticRegression --extended-experiments --extended-models LogisticRegression --bootstrap-rounds 0
```

Expected: baseline LogisticRegression runs and extended experiment tables are written.

Actual: smoke testing was run with `--extended-only` and selected models after adding the flag, then the full selected extended run was executed.

### Task 4: Run Planned Experiments

**Files:**
- Generate/modify: `outputs/tables/icu_28d_mortality_ablation_performance.csv`
- Generate/modify: `outputs/tables/icu_28d_mortality_missingness_performance.csv`
- Generate/modify: `outputs/tables/icu_28d_mortality_calibration_comparison.csv`
- Generate/modify: `outputs/tables/icu_28d_mortality_risk_bins.csv`
- Generate/modify: `outputs/tables/icu_28d_mortality_shap_stability.csv`
- Modify: `outputs/docs/EXPERIMENT_RECORD.md`

- [x] **Step 1: Run extended experiments**

Run:

```bash
.venv/bin/python run.py --train-only --extended-experiments --extended-only --extended-models HistGradientBoosting XGBoost LightGBM --shap-stability-sample-size 300 --shap-stability-repeats 3
```

Expected: extended tables are produced.

- [x] **Step 2: Summarize outputs**

Update `outputs/docs/EXPERIMENT_RECORD.md` with:
- command used;
- generated tables;
- high-level interpretation placeholders based only on produced metrics.

### Task 5: Verification

**Files:**
- Check: code, tests, generated outputs

- [x] **Step 1: Run unit tests**

Run:

```bash
.venv/bin/python tests/test_experiments.py
```

Expected: all tests pass.

- [x] **Step 2: Verify output tables exist and have rows**

Run:

```bash
.venv/bin/python -c "from pathlib import Path; import pandas as pd; paths=['outputs/tables/icu_28d_mortality_ablation_performance.csv','outputs/tables/icu_28d_mortality_missingness_performance.csv','outputs/tables/icu_28d_mortality_calibration_comparison.csv','outputs/tables/icu_28d_mortality_risk_bins.csv','outputs/tables/icu_28d_mortality_shap_stability.csv']; [print(p, pd.read_csv(p).shape) for p in paths if Path(p).exists()]"
```

Expected: five table paths printed with non-zero row counts.
