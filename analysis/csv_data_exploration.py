from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

import pandas as pd

# Ensure repo root is on sys.path when running via absolute path
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from services.substitution_service.data_loaders import (  # noqa: E402
    DEFAULT_PURCHASES_CSV,
    DEFAULT_REPLACEMENTS_CSV,
    DEFAULT_SALES_DELIVERIES_CSV,
    get_data_dir,
)


def sample_csv(file_path: Path, nrows: int = 100000) -> pd.DataFrame:
    return pd.read_csv(file_path, nrows=nrows)


def non_null_ratios(df: pd.DataFrame, top_k: int = 200) -> List[Tuple[str, float]]:
    ratios = (1.0 - df.isna().mean()).sort_values(ascending=False)
    items = [(col, float(ratios[col])) for col in ratios.index[:top_k]]
    return items


def infer_candidate_fields(columns: Iterable[str]) -> Dict[str, List[str]]:
    signals = {
        "sku": ["sku", "product", "item", "gtin", "ean", "code"],
        "order": ["order", "order_id", "orderline", "line_id"],
        "customer": ["customer", "client", "account", "buyer"],
        "supplier": ["supplier", "vendor"],
        "category": ["category", "group", "segment", "family"],
        "date": ["date", "day", "time", "timestamp"],
        "qty": ["qty", "quantity", "units", "amount"],
        "delivered": ["delivered", "deliv", "shipped", "fulfilled"],
        "price": ["price", "cost", "value"],
    }
    cols_lower = {c: c.lower() for c in columns}
    matches: Dict[str, List[str]] = {k: [] for k in signals}
    for k, keys in signals.items():
        for col, col_l in cols_lower.items():
            if any(sig in col_l for sig in keys):
                matches[k].append(col)
    return matches


def top_value_counts(df: pd.DataFrame, cols: List[str], top_n: int = 20) -> Dict[str, List[Tuple[str, int]]]:
    out: Dict[str, List[Tuple[str, int]]] = {}
    for c in cols:
        if c in df.columns:
            vc = df[c].astype(str).value_counts(dropna=True).head(top_n)
            out[c] = list(zip(vc.index.tolist(), vc.values.tolist()))
    return out


def write_report(
    title: str,
    filename: str,
    df: pd.DataFrame,
    file_path: Path,
    field_matches: Dict[str, List[str]],
    category_cols: List[str],
    sample_rows: int = 5,
) -> None:
    lines: List[str] = []
    lines.append(f"# {title}")
    lines.append("")
    lines.append(f"- File: `{file_path.name}`")
    lines.append(f"- Sampled rows: {len(df)}")
    lines.append("")
    lines.append("## Dtypes")
    lines.append("")
    lines.append("| column | dtype |")
    lines.append("|---|---|")
    for col, dtype in df.dtypes.items():
        lines.append(f"| {col} | {str(dtype)} |")
    lines.append("")
    lines.append("## Non-null ratios (top)")
    lines.append("")
    lines.append("| column | non_null_ratio |")
    lines.append("|---|---|")
    for col, ratio in non_null_ratios(df):
        lines.append(f"| {col} | {ratio:.3f} |")
    lines.append("")
    lines.append("## Candidate fields (auto-detected)")
    lines.append("")
    for k, cols in field_matches.items():
        if cols:
            lines.append(f"- {k}: {', '.join(cols)}")
    lines.append("")
    if category_cols:
        lines.append("## Top values for selected categorical/id columns")
        lines.append("")
        tvc = top_value_counts(df, category_cols, top_n=20)
        for c, pairs in tvc.items():
            lines.append(f"### {c}")
            lines.append("")
            lines.append("| value | count |")
            lines.append("|---|---|")
            for v, cnt in pairs:
                # Restrict extremely long strings for readability
                v_str = v if len(v) <= 120 else (v[:117] + "...")
                lines.append(f"| {v_str} | {cnt} |")
            lines.append("")
    lines.append("## Sample rows")
    lines.append("")
    preview = df.head(sample_rows).to_dict(orient="records")
    pretty = json.dumps(preview, ensure_ascii=False, indent=2)
    lines.append("```json")
    lines.append(pretty)
    lines.append("```")
    out_path = Path("Docs") / filename
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    data_dir = get_data_dir()

    tasks = [
        (
            "Replacement Orders Exploration",
            "replacement_orders_exploration.md",
            data_dir / DEFAULT_REPLACEMENTS_CSV,
        ),
        (
            "Sales & Deliveries Exploration",
            "sales_deliveries_exploration.md",
            data_dir / DEFAULT_SALES_DELIVERIES_CSV,
        ),
        (
            "Purchases Exploration",
            "purchases_exploration.md",
            data_dir / DEFAULT_PURCHASES_CSV,
        ),
    ]

    for title, out_name, path in tasks:
        df = sample_csv(path, nrows=100_000)
        matches = infer_candidate_fields(df.columns)
        cat_cols: List[str] = []
        for key in ("sku", "supplier", "category", "customer"):
            cat_cols.extend(matches.get(key, []))
        # De-duplicate while preserving order
        seen = set()
        cat_cols = [c for c in cat_cols if not (c in seen or seen.add(c))]
        write_report(
            title=title,
            filename=out_name,
            df=df,
            file_path=path,
            field_matches=matches,
            category_cols=cat_cols[:6],  # limit number of columns to summarize
        )


if __name__ == "__main__":
    main()


