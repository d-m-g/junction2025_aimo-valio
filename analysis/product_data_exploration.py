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

from services.substitution_service.data_loaders import (
    DEFAULT_PRODUCT_JSON,
    get_data_dir,
)


def _stream_json_array_sample(file_path: Path, max_items: int = 5000) -> pd.DataFrame:
    """
    Stream-parse a JSON array file and return up to max_items objects as a DataFrame.
    Avoids loading the entire 200MB+ file into memory.
    """
    records: List[dict] = []
    with file_path.open("r", encoding="utf-8") as f:
        # Seek to first '['
        ch = f.read(1)
        while ch and ch.isspace():
            ch = f.read(1)
        if ch != "[":
            # Not an array JSON; bail out
            raise ValueError("Expected JSON array starting with '['")
        in_string = False
        escape = False
        brace_depth = 0
        buf_chars: List[str] = []
        while True:
            ch = f.read(1)
            if not ch:
                break
            if in_string:
                buf_chars.append(ch)
                if escape:
                    escape = False
                elif ch == "\\":
                    escape = True
                elif ch == '"':
                    in_string = False
                continue
            # not in string
            if brace_depth == 0:
                if ch == "{":
                    brace_depth = 1
                    buf_chars = ["{"]
                elif ch == "]":
                    break
                else:
                    # skip commas/whitespace between objects
                    continue
            else:
                buf_chars.append(ch)
                if ch == '"':
                    in_string = True
                    escape = False
                elif ch == "{":
                    brace_depth += 1
                elif ch == "}":
                    brace_depth -= 1
                    if brace_depth == 0:
                        try:
                            rec = json.loads("".join(buf_chars))
                            if isinstance(rec, dict):
                                records.append(rec)
                        except json.JSONDecodeError:
                            pass
                        if len(records) >= max_items:
                            break
                        buf_chars = []
        if not records:
            raise ValueError("No objects parsed from JSON array")
    return pd.DataFrame.from_records(records)


def read_json_lines_sample(file_path: Path, max_lines: int = 50000) -> pd.DataFrame:
    """
    Efficiently sample first N lines from a JSON Lines file into a DataFrame.
    Falls back to incremental per-line parsing or streaming array parsing if needed.
    """
    try:
        return pd.read_json(file_path, lines=True, nrows=max_lines)  # JSONL fast path
    except Exception:
        # Manual per-line parse
        records: List[dict] = []
        with file_path.open("r", encoding="utf-8") as f:
            # Peek first non-whitespace char to detect array JSON
            head = f.read(256)
            f.seek(0)
            for c in head:
                if not c.isspace():
                    if c == "[":
                        # Stream parse array JSON sample
                        return _stream_json_array_sample(file_path, max_items=min(5000, max_lines))
                    break
            for idx, line in enumerate(f):
                if idx >= max_lines:
                    break
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                    if isinstance(rec, dict):
                        records.append(rec)
                except json.JSONDecodeError:
                    # Not JSONL; try array streaming parse instead
                    return _stream_json_array_sample(file_path, max_items=min(5000, max_lines))
        if records:
            return pd.DataFrame.from_records(records)
        # Final fallback: try full-file JSON (may be memory-heavy)
        try:
            full = pd.read_json(file_path)
            return full
        except Exception as e:
            raise e


def infer_candidate_feature_fields(columns: Iterable[str]) -> Dict[str, List[str]]:
    signals = {
        "sku": ["sku", "product_code", "id", "gtin", "ean"],
        "name": ["name", "title", "product_name"],
        "description": ["description", "desc", "long_description", "short_description"],
        "category": ["category", "subcategory", "group", "segment"],
        "brand": ["brand", "manufacturer", "producer", "label"],
        "supplier": ["supplier", "vendor"],
        "allergens": ["allergen", "allergens"],
        "dietary": ["diet", "dietary", "lactose", "gluten", "vegan", "vegetarian"],
        "temperature": ["temperature", "temp_class", "storage"],
        "pack": ["pack", "package", "pack_size", "unit_size", "size", "volume", "weight"],
        "unit": ["unit", "uom", "measure"],
        "price": ["price", "list_price", "unit_price"],
    }
    cols_lower = {c: c.lower() for c in columns}
    matches: Dict[str, List[str]] = {k: [] for k in signals}
    for k, keys in signals.items():
        for col, col_l in cols_lower.items():
            if any(sig in col_l for sig in keys):
                matches[k].append(col)
    return matches


def non_null_ratios(df: pd.DataFrame, top_k: int = 200) -> List[Tuple[str, float]]:
    ratios = (1.0 - df.isna().mean()).sort_values(ascending=False)
    items = [(col, float(ratios[col])) for col in ratios.index[:top_k]]
    return items


def write_markdown_report(
    df: pd.DataFrame,
    feature_matches: Dict[str, List[str]],
    out_path: Path,
    sample_rows: int = 5,
) -> None:
    lines: List[str] = []
    lines.append("# Product Data Exploration (Sample)")
    lines.append("")
    lines.append(f"- File: `{DEFAULT_PRODUCT_JSON}`")
    lines.append(f"- Sample size: {len(df)} rows")
    lines.append("")
    lines.append("## Columns and non-null ratios (top)")
    lines.append("")
    lines.append("| column | non_null_ratio |")
    lines.append("|---|---|")
    for col, ratio in non_null_ratios(df):
        lines.append(f"| {col} | {ratio:.3f} |")
    lines.append("")
    lines.append("## Candidate feature fields (auto-detected)")
    lines.append("")
    for k, cols in feature_matches.items():
        if cols:
            lines.append(f"- {k}: {', '.join(cols)}")
    lines.append("")
    lines.append("## Sample rows")
    lines.append("")
    preview = df.head(sample_rows).to_dict(orient="records")
    pretty = json.dumps(preview, ensure_ascii=False, indent=2)
    lines.append("```json")
    lines.append(pretty)
    lines.append("```")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    data_dir = get_data_dir()
    file_path = data_dir / DEFAULT_PRODUCT_JSON
    df = read_json_lines_sample(file_path, max_lines=50000)
    feature_matches = infer_candidate_feature_fields(df.columns)
    write_markdown_report(
        df=df,
        feature_matches=feature_matches,
        out_path=Path("Docs/product_data_exploration.md"),
    )


if __name__ == "__main__":
    main()


