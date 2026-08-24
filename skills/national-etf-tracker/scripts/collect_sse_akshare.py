#!/usr/bin/env python3
"""Collect daily SSE ETF shares from AKShare's date-based SSE endpoint."""
from __future__ import annotations
import argparse
from pathlib import Path
import pandas as pd

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--start-date", required=True, help="YYYY-MM-DD or YYYYMMDD")
    ap.add_argument("--end-date", required=True, help="YYYY-MM-DD or YYYYMMDD")
    ap.add_argument("--output", required=True)
    ap.add_argument("--raw-dir", help="optional directory for one raw CSV per date")
    args = ap.parse_args()
    try:
        import akshare as ak
    except ImportError as e:
        raise SystemExit("未安装 akshare，请先执行: pip install akshare") from e
    start, end = pd.Timestamp(args.start_date), pd.Timestamp(args.end_date)
    frames, errors = [], []
    for day in pd.bdate_range(start, end):
        stamp = day.strftime("%Y%m%d")
        try:
            raw = ak.fund_etf_scale_sse(date=stamp)
            required = {"统计日期", "基金代码", "基金简称", "基金份额"}
            if raw is None or raw.empty or not required.issubset(raw.columns): continue
            if args.raw_dir:
                p = Path(args.raw_dir); p.mkdir(parents=True, exist_ok=True)
                raw.to_csv(p / f"sse_etf_scale_{stamp}.csv", index=False, encoding="utf-8-sig")
            out = raw.rename(columns={"统计日期":"date", "基金代码":"code", "基金简称":"name", "基金份额":"shares"}).copy()
            out["date"] = pd.to_datetime(out["date"], errors="coerce").dt.strftime("%Y-%m-%d")
            out["code"] = out["code"].astype(str).str.extract(r"(\d{6})", expand=False)
            out["shares"] = pd.to_numeric(out["shares"], errors="coerce")
            out["share_unit"] = "份"; out["source"] = "akshare_fund_etf_scale_sse"; out["market"] = "SH"; out["close"] = pd.NA; out["industry"] = pd.NA; out["source_file"] = f"akshare:{stamp}"
            frames.append(out[["date","source","market","code","name","shares","share_unit","close","industry","source_file"]])
        except Exception as exc:
            errors.append(f"{stamp}: {exc}")
    if not frames: raise SystemExit("AKShare 沪市 ETF 接口未返回数据。错误: " + " | ".join(errors[-3:]))
    result = pd.concat(frames, ignore_index=True).dropna(subset=["date","code","shares"]).drop_duplicates(["date","market","code"], keep="last").sort_values(["date","code"])
    target = Path(args.output); target.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(target, index=False, encoding="utf-8-sig")
    print(f"已保存 {len(result)} 行沪市 ETF 份额数据: {target}")
    if errors: print(f"警告：{len(errors)} 个日期失败，示例: {errors[-1]}")

if __name__ == "__main__": main()
