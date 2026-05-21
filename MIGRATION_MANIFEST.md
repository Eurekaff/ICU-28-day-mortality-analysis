# Migration Manifest

This project was extracted from `E:\thesis_ad_icu` as an independent prolonged ICU length-of-stay experiment.

Migrated code:

- `build_dataset.py`
- `train_eval.py`
- `run.py`
- `write_paper_draft.py`
- `settings.py`
- `model_specs.py`
- `io_utils.py`

Migrated input data:

- `data/processed/ch3_analysis_dataset.parquet`

Migrated experiment outputs:

- `data/processed/prolonged_icu_los_*`
- `outputs/tables/prolonged_icu_los_*`
- `outputs/figures/prolonged_icu_los_*`

Migrated documents:

- Existing prolonged ICU LOS paper draft from the original `docs` directory, when present.

The project no longer imports `config.settings`, `src.utils`, or `src.modeling` from the original repository. By default it reads and writes only inside this project directory.
