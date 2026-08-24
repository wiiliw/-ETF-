#!/usr/bin/env python3
"""Run yearly/semiannual collectors and merge all available canonical files."""
from __future__ import annotations
import argparse, subprocess, sys
from datetime import date
from pathlib import Path


def run(cmd: list[str]) -> None:
    print("+", " ".join(cmd), flush=True)
    subprocess.run(cmd, check=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--start-year", type=int, default=2024)
    ap.add_argument("--end-date", default=date.today().isoformat())
    ap.add_argument("--root", default="skills/national-etf-tracker")
    args = ap.parse_args()
    root = Path(args.root); raw = root / "data/raw/annual"; raw.mkdir(parents=True, exist_ok=True)
    end = date.fromisoformat(args.end_date)
    py = sys.executable
    sse = root / "scripts/collect_sse_akshare.py"
    szse = root / "scripts/collect_szse_akshare.py"
    inputs: list[str] = []
    for year in range(args.start_year, end.year + 1):
        print(f"=== collecting year {year} ===", flush=True)
        y_end = min(date(year, 12, 31), end)
        intervals = [(date(year, 1, 1), min(date(year, 6, 30), y_end)), (date(year, 7, 1), y_end)]
        sse_out = raw / f"sse_{year}.csv"
        if not sse_out.exists():
            run([py, str(sse), "--start-date", date(year, 1, 1).isoformat(), "--end-date", y_end.isoformat(), "--output", str(sse_out)])
        else:
            print(f"skip existing {sse_out}", flush=True)
        inputs.append(str(sse_out))
        for part, (start, finish) in enumerate(intervals, 1):
            if start > finish: continue
            out = raw / f"szse_{year}_h{part}.csv"
            if not out.exists():
                run([py, str(szse), "--start-date", start.isoformat(), "--end-date", finish.isoformat(), "--output", str(out)])
            else:
                print(f"skip existing {out}", flush=True)
            inputs.append(str(out))
    merge = root / "scripts/merge_sources.py"
    run([py, str(merge), "--inputs", *inputs, "--output", str(root / "data/processed/etf_shares.csv"), "--report", str(root / "data/processed/quality_report.json")])


if __name__ == "__main__": main()
