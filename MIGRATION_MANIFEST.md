# Project Manifest

This project is an independent ICU 28-day mortality prediction experiment.

Core code:

- `build_dataset.py`
- `train_eval.py`
- `run.py`
- `write_paper_draft.py`
- `settings.py`
- `model_specs.py`
- `io_utils.py`

Input data:

- `data/processed/ch3_analysis_dataset.parquet`

Current experiment outputs:

- `data/processed/icu_28d_mortality_*`
- `outputs/tables/icu_28d_mortality_*`
- `outputs/figures/icu_28d_mortality_*`
- `outputs/docs/基于MIMIC-IV的ICU患者28天死亡风险预测研究_论文初稿.docx`

The project reads and writes inside this project directory by default. Use `ICU_MORTALITY_INPUT_DIR` only when a different processed-data input directory is needed.
