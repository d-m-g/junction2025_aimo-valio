import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Optional, Sequence

import pandas as pd
from dotenv import load_dotenv


DEFAULT_PRODUCT_JSON = "valio_aimo_product_data_junction_2025.json"
DEFAULT_REPLACEMENTS_CSV = "valio_aimo_replacement_orders_junction_2025.csv"
DEFAULT_SALES_DELIVERIES_CSV = "valio_aimo_sales_and_deliveries_junction_2025.csv"
DEFAULT_PURCHASES_CSV = "valio_aimo_purchases_junction_2025.csv"


def get_data_dir() -> Path:
    """
    Resolve the data directory from environment variable VALIO_DATA_DIR or default to repo_root/Data.
    """
    load_dotenv()
    configured = os.getenv("VALIO_DATA_DIR")
    if configured:
        return Path(configured).expanduser().resolve()
    # repo root is two levels above this file: services/substitution_service/ -> repo_root
    return Path(__file__).resolve().parents[2] / "Data"


def _resolve_path(path_or_dir: Optional[Path], default_filename: str) -> Path:
    """
    If a file path is provided, return it. If a directory or None is provided, append default_filename.
    """
    if path_or_dir is None:
        return (get_data_dir() / default_filename).resolve()
    path = Path(path_or_dir)
    if path.is_dir():
        return (path / default_filename).resolve()
    return path.resolve()


def load_product_data_json(
    path_or_dir: Optional[Path] = None,
    usecols: Optional[Sequence[str]] = None,
) -> pd.DataFrame:
    """
    Load product data JSON. Tries JSON Lines first, then array JSON.
    """
    file_path = _resolve_path(path_or_dir, DEFAULT_PRODUCT_JSON)
    try:
        df = pd.read_json(file_path, lines=True)
    except ValueError:
        df = pd.read_json(file_path)
    if usecols:
        existing = [c for c in usecols if c in df.columns]
        if existing:
            df = df[existing]
    return df


def load_replacement_orders_csv(
    path_or_dir: Optional[Path] = None,
    usecols: Optional[Sequence[str]] = None,
    dtype: Optional[Dict[str, Any]] = None,
) -> pd.DataFrame:
    """
    Load replacement orders CSV (historical original->replacement pairs).
    """
    file_path = _resolve_path(path_or_dir, DEFAULT_REPLACEMENTS_CSV)
    return pd.read_csv(file_path, usecols=usecols, dtype=dtype)


def load_sales_deliveries_csv(
    path_or_dir: Optional[Path] = None,
    usecols: Optional[Sequence[str]] = None,
    dtype: Optional[Dict[str, Any]] = None,
) -> pd.DataFrame:
    """
    Load sales & deliveries CSV (ordered vs delivered, product-level stats).
    """
    file_path = _resolve_path(path_or_dir, DEFAULT_SALES_DELIVERIES_CSV)
    return pd.read_csv(file_path, usecols=usecols, dtype=dtype)


def load_purchases_csv(
    path_or_dir: Optional[Path] = None,
    usecols: Optional[Sequence[str]] = None,
    dtype: Optional[Dict[str, Any]] = None,
) -> pd.DataFrame:
    """
    Load purchases CSV (supplier patterns, lead times, partial deliveries).
    """
    file_path = _resolve_path(path_or_dir, DEFAULT_PURCHASES_CSV)
    return pd.read_csv(file_path, usecols=usecols, dtype=dtype)


# Cached convenience wrappers (use defaults)
@lru_cache(maxsize=1)
def product_data_df() -> pd.DataFrame:
    return load_product_data_json()


@lru_cache(maxsize=1)
def replacement_orders_df() -> pd.DataFrame:
    return load_replacement_orders_csv()


@lru_cache(maxsize=1)
def sales_deliveries_df() -> pd.DataFrame:
    return load_sales_deliveries_csv()


@lru_cache(maxsize=1)
def purchases_df() -> pd.DataFrame:
    return load_purchases_csv()


