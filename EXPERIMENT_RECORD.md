# Experiment Record

Task: predict prolonged ICU stay among AD ICU patients.

Default outcome:

```text
prolonged_icu_los = 1 if icu_los_days > 7 else 0
```

Default cohort rule:

- AD ICU patients only.
- ICU length of stay must be available.
- ICU length of stay must be at least 24 hours.

Default feature set:

- Demographics: age, gender, race group.
- ICU admission unit: first care unit.
- First 24-hour vitals and labs, including HR, RR, SpO2, SBP, DBP, MAP, WBC, hemoglobin, platelets, electrolytes, renal function, coagulation, lactate, bilirubin, albumin, and GCS features when available.

Modeling workflow:

1. Build the prolonged ICU LOS modeling dataset from `data/processed/ch3_analysis_dataset.parquet`.
2. Create baseline summary by outcome group.
3. Compare machine-learning models with stratified train-test split and stratified cross-validation.
4. Save performance tables, threshold metrics, confusion matrix, ROC/PR/calibration figures, best model, test predictions, and model metadata.

Independent smoke-test command:

```powershell
python -m prolonged_icu_los_experiment.run --models LogisticRegression DecisionTree --bootstrap-rounds 0
```
