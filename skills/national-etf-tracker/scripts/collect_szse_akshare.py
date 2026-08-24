#!/usr/bin/env python3
"""Collect Shenzhen ETF daily shares via AKShare's <=6-month interval API."""
from __future__ import annotations
import argparse
from pathlib import Path
import pandas as pd

MAX_DAYS = 184

def normalize(raw: pd.DataFrame) -> pd.DataFrame:
    rename = {"日期":"date", "基金代码":"code", "基金简称":"name", "基金份额":"shares"}
    out = raw.rename(columns=rename).copy()
    required = {"date", "code", "shares"}
    missing = required - set(out.columns)
    if missing: raise ValueError(f"深市接口缺少字段 {missing}; 实际字段: {list(raw.columns)}")
    out["date"] = pd.to_datetime(out["date"], errors="coerce").dt.strftime("%Y-%m-%d")
    out["code"] = out["code"].astype(str).str.extract(r"(\d{6})", expand=False)
    out["shares"] = pd.to_numeric(out["shares"], errors="coerce")
    out["share_unit"] = "份"
    out["source"] = "akshare_fund_scale_daily_szse"
    out["market"] = "SZ"
    out["close"] = pd.NA
    out["industry"] = pd.NA
    out["source_file"] = "akshare:szse_daily"
    return out[["date","source","market","code","name","shares","share_unit","close","industry","source_file"]]

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--start-date", required=True, help="YYYY-MM-DD")
    ap.add_argument("--end-date", required=True, help="YYYY-MM-DD; interval <= 6 months")
    ap.add_argument("--output", required=True)
    args = ap.parse_args()
    start, end = pd.Timestamp(args.start_date), pd.Timestamp(args.end_date)
    if end < start: raise SystemExit("end-date 不能早于 start-date")
    if (end - start).days > MAX_DAYS: raise SystemExit("深交所接口单次区间不得超过约 6 个月，请拆分调用")
    try:
        import akshare as ak
    except ImportError as e:
        raise SystemExit("未安装 akshare，请先执行: pip install akshare") from e
    fn = getattr(ak, "fund_scale_daily_szse", None)
    if fn is None: raise SystemExit("当前 AKShare 没有 fund_scale_daily_szse；建议升级到 >= 1.18.52")
    raw = fn(start_date=start.strftime("%Y%m%d"), end_date=end.strftime("%Y%m%d"), symbol="ETF")
    if raw is None or raw.empty: raise SystemExit("深交所接口返回空数据")
    result = normalize(raw).dropna(subset=["date","code","shares"]).drop_duplicates(["date","market","code"])
    target = Path(args.output); target.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(target, index=False, encoding="utf-8-sig")
    print(f"已保存 {len(result)} 行深市 ETF 份额数据: {target}")

if __name__ == "__main__": main()
