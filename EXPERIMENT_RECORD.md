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
4. Save performance tables, threshold metrics, confusion matrix, ROC/PR/calibration figures, best model, test predictions, and model metadata.

Full command:

```powershell
python run.py
```

Independent smoke-test command:

```powershell
python run.py --models LogisticRegression DecisionTree --bootstrap-rounds 0
```
