#!/usr/bin/env python3
"""Merge canonical share CSV files, deduplicate keys, and emit a quality report."""
from __future__ import annotations
import argparse, json
from pathlib import Path
import pandas as pd

FIELDS = ["date","source","market","code","name","shares","share_unit","close","industry","source_file"]

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--inputs", nargs="+", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--report", required=True)
    args = ap.parse_args()
    frames = []
    for item in args.inputs:
        p = Path(item)
        if p.exists(): frames.append(pd.read_csv(p, dtype={"code": str}))
    if not frames: raise SystemExit("没有可合并的输入文件")
    df = pd.concat(frames, ignore_index=True)
    for field in FIELDS:
        if field not in df: df[field] = pd.NA
    df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.strftime("%Y-%m-%d")
    df["code"] = df["code"].astype(str).str.extract(r"(\d{6})", expand=False)
    df["shares"] = pd.to_numeric(df["shares"], errors="coerce")
    df["share_unit"] = df["share_unit"].fillna("份")
    before = len(df)
    invalid = int(df[["date","code","shares"]].isna().any(axis=1).sum())
    df = df.dropna(subset=["date","code","shares"])
    duplicate_keys = int(df.duplicated(["date","market","code"], keep=False).sum())
    df = df.drop_duplicates(["date","market","code"], keep="last").sort_values(["date","market","code"])
    target = Path(args.output); target.parent.mkdir(parents=True, exist_ok=True)
    df[FIELDS].to_csv(target, index=False, encoding="utf-8-sig")
    report = {"input_rows": before, "output_rows": len(df), "invalid_rows_dropped": invalid, "duplicate_key_rows_seen": duplicate_keys, "date_min": df.date.min(), "date_max": df.date.max(), "markets": df.market.value_counts(dropna=False).to_dict(), "files": [str(x) for x in args.inputs]}
    Path(args.report).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))

if __name__ == "__main__": main()
