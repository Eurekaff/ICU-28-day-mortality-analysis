# Experiment Record

Task: predict 28-day mortality among ICU patients.

Default outcome:

```text
death_28d = 1 if the patient died within 28 days after ICU admission else 0
```

Default cohort rule:

- ICU patients from `ch3_analysis_dataset`.
- ICU length of stay must be available.
- ICU length of stay must be at least 24 hours.
- The 28-day mortality label must be available.

Default feature set:

- Demographics: age, gender, race group.
- ICU admission unit: first care unit.
- First 24-hour vitals: HR, RR, SpO2, SBP, DBP, MAP, and temperature.
- First 24-hour labs: WBC, hemoglobin, platelets, electrolytes, renal function, glucose, anion gap, coagulation features, and related summary statistics when available.

Modeling workflow:

1. Build the ICU 28-day mortality modeling dataset from `data/processed/ch3_analysis_dataset.parquet`.
2. Create baseline summary by 28-day mortality group.
3. Compare machine-learning models with stratified train-test split and stratified cross-validation.
4. Save performance tables, threshold metrics, confusion matrix, ROC/PR/calibration figures, SHAP explanations, best model, test predictions, and model metadata.

Full command:

```powershell
python run.py
```

Independent smoke-test command:

```powershell
python run.py --models LogisticRegression DecisionTree --bootstrap-rounds 0
```

## 2026-06-04 Extended Experiment Run

Purpose: execute the redesigned experiment plan that supports the paper's innovation narrative. The run adds four experiment blocks beyond the ordinary model leaderboard:

- feature-source and feature-window ablation;
- missingness indicators and group-level missingness burden;
- calibration comparison with uncalibrated, sigmoid, and isotonic probabilities;
- SHAP top-feature stability under repeated subsampling.

Implementation entry points:

- `src/icu_mortality/experiments.py`
- `run.py --extended-experiments`

Commands executed:

```bash
.venv/bin/python tests/test_experiments.py
.venv/bin/python run.py --train-only
.venv/bin/python run.py --train-only --extended-experiments --extended-only --extended-models HistGradientBoosting XGBoost LightGBM --shap-stability-sample-size 300 --shap-stability-repeats 3
```

Generated extended tables:

- `outputs/tables/icu_28d_mortality_ablation_performance.csv` `(18, 13)`
- `outputs/tables/icu_28d_mortality_missingness_performance.csv` `(6, 13)`
- `outputs/tables/icu_28d_mortality_calibration_comparison.csv` `(9, 11)`
- `outputs/tables/icu_28d_mortality_risk_bins.csv` `(45, 8)`
- `outputs/tables/icu_28d_mortality_shap_stability.csv` `(20, 6)`

Baseline rerun summary:

- Best model: LightGBM.
- Test AUROC: 0.874188.
- Test AUPRC: 0.555967.
- Test Brier: 0.131608.

Extended experiment findings:

- Feature ablation shows the full feature set performs best among tested subsets. Best full-set AUROC is LightGBM `0.870939`; best summary-only AUROC is HistGradientBoosting `0.857922`, suggesting compact first-24h summary features retain most signal.
- Lab-only features are stronger than vitals-only and demographics-only features. Best lab-only AUROC is LightGBM `0.818575`; best vitals-only AUROC is LightGBM `0.766921`; best demographics-only AUROC is HistGradientBoosting `0.758067`.
- Missingness-aware features improve discrimination for all three selected tree models. HistGradientBoosting AUROC improves from `0.869661` to `0.871050`; XGBoost from `0.859609` to `0.861014`; LightGBM from `0.870939` to `0.871774`.
- Missingness-aware features also improve AUPRC. HistGradientBoosting AUPRC improves from `0.540135` to `0.553812`; XGBoost from `0.524081` to `0.531047`; LightGBM from `0.544564` to `0.550702`.
- Calibration comparison favors calibrated HistGradientBoosting by Brier score. HistGradientBoosting with sigmoid calibration has Brier `0.082781`, AUROC `0.873057`, AUPRC `0.552572`, and F1 `0.532275`.
- LightGBM benefits strongly from probability calibration in Brier score: uncalibrated Brier `0.136094`, isotonic Brier `0.083199`.
- SHAP stability identifies the same top-10 features for XGBoost and LightGBM across 3 repeated subsamples: `anchor_age`, `anion_gap_mean`, `bun_max`, `bun_mean`, `cl_first`, `first_careunit_CVICU`, `race_group_Unknown`, `rr_mean`, `spo2_mean`, and `spo2_min`.

Notes:

- `pytest` is not installed in the current virtual environment, so the helper tests were written as plain Python assertions and run with `.venv/bin/python tests/test_experiments.py`.
- Runtime warnings from pyarrow CPU detection, sklearn calibration, LightGBM feature-name checks, and SHAP LightGBM output format were observed. They did not stop table generation.
