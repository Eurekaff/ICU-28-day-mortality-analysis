from __future__ import annotations

from pathlib import Path

import pandas as pd


def save_df(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.suffix == ".parquet":
        try:
            df.to_parquet(path, index=False)
            return
        except Exception:
            df.to_csv(path.with_suffix(".csv"), index=False)
            return
    df.to_csv(path, index=False)


def load_df(path: Path) -> pd.DataFrame:
    if path.suffix == ".parquet":
        return pd.read_parquet(path)
    return pd.read_csv(path)
