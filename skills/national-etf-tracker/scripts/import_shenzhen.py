#!/usr/bin/env python3
"""Import Shenzhen exchange ETF share files into the project's canonical CSV."""
from __future__ import annotations
import argparse
from pathlib import Path
import pandas as pd

ALIASES = {
    "date": ["date", "日期", "交易日期", "交易日"],
    "code": ["code", "证券代码", "基金代码", "代码"],
    "name": ["name", "证券简称", "基金简称", "简称", "名称"],
    "shares": ["shares", "基金份额", "份额", "份额(份)", "基金份额(份)"],
    "close": ["close", "收盘价", "收盘价(元)", "单位净值"],
}

def read_any(path: Path) -> pd.DataFrame:
    if path.suffix.lower() in {".xls", ".xlsx"}:
        return pd.read_excel(path)
    for enc in ("utf-8-sig", "gb18030", "utf-8"):
        try:
            return pd.read_csv(path, encoding=enc, sep=None, engine="python")
        except UnicodeDecodeError:
            continue
    raise ValueError(f"无法读取文件编码: {path}")

def normalize(df: pd.DataFrame, source_file: str) -> pd.DataFrame:
    rename = {}
    for standard, names in ALIASES.items():
        found = next((c for c in df.columns if str(c).strip() in names), None)
        if found is None and standard in {"date", "code", "shares"}:
            raise ValueError(f"{source_file} 缺少必要列 {standard}; 实际列: {list(df.columns)}")
        if found is not None:
            rename[found] = standard
    out = df.rename(columns=rename).copy()
    out["date"] = pd.to_datetime(out["date"], errors="coerce").dt.strftime("%Y-%m-%d")
    out["code"] = out["code"].astype(str).str.extract(r"(\d{6})", expand=False)
    out["shares"] = pd.to_numeric(out["shares"].astype(str).str.replace(",", ""), errors="coerce")
    if "close" not in out: out["close"] = pd.NA
    out["close"] = pd.to_numeric(out["close"], errors="coerce")
    if "name" not in out: out["name"] = pd.NA
    out["source"] = "shenzhen_exchange_file"
    out["market"] = "SZ"
    out["industry"] = pd.NA
    out["source_file"] = source_file
    out["share_unit"] = "份"
    return out[["date","source","market","code","name","shares","share_unit","close","industry","source_file"]]

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input-dir", required=True)
    ap.add_argument("--output", default="skills/national-etf-tracker/data/processed/etf_shares.csv")
    args = ap.parse_args()
    files = [p for p in Path(args.input_dir).rglob("*") if p.suffix.lower() in {".csv", ".txt", ".xls", ".xlsx"}]
    if not files: raise SystemExit("输入目录没有 CSV/XLS/XLSX/TSV 文件")
    frames = [normalize(read_any(p), str(p)) for p in files]
    out = pd.concat(frames, ignore_index=True)
    target = Path(args.output); target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists(): out = pd.concat([pd.read_csv(target), out], ignore_index=True)
    out = out.dropna(subset=["date", "code", "shares"]).drop_duplicates(["date", "market", "code"], keep="last").sort_values(["date","market","code"])
    out.to_csv(target, index=False, encoding="utf-8-sig")
    print(f"导入 {len(files)} 个文件，写入 {len(out)} 行: {target}")

if __name__ == "__main__": main()
