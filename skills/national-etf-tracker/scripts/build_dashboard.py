#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from pathlib import Path
import pandas as pd

COLS = ["date","source","market","code","name","shares","share_unit","close","industry","source_file"]

def main() -> None:
    ap = argparse.ArgumentParser(description="Build industry ETF share-flow CSV and offline HTML dashboard")
    ap.add_argument("--input", required=True)
    ap.add_argument("--mapping", required=True)
    ap.add_argument("--output-dir", required=True)
    args = ap.parse_args()
    outdir = Path(args.output_dir); outdir.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(args.input, dtype={"code": str})
    for c in COLS:
        if c not in df: df[c] = pd.NA
    df["code"] = df["code"].astype(str).str.extract(r"(\d{6})", expand=False)
    mapping = pd.read_csv(args.mapping, dtype={"code": str}).drop_duplicates("code")
    df = df.drop(columns=["industry"], errors="ignore").merge(mapping[["code","industry"]], on="code", how="left")
    df["industry"] = df["industry"].fillna("未分类")
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["shares"] = pd.to_numeric(df["shares"], errors="coerce")
    df["close"] = pd.to_numeric(df["close"], errors="coerce")
    before = len(df)
    df = df.dropna(subset=["date","code","shares"]).sort_values(["code","date"])
    duplicate_count = int(df.duplicated(["date","market","code"]).sum())
    df = df.drop_duplicates(["date","market","code"], keep="last")
    df["shares_change"] = df.groupby("code")["shares"].diff()
    df["shares_change_pct"] = df["shares_change"] / df.groupby("code")["shares"].shift(1).abs()
    df["cash_proxy"] = df["shares_change"] * df.groupby("code")["close"].shift(1)
    df["date"] = df["date"].dt.strftime("%Y-%m-%d")
    daily = df.groupby(["date","industry"], as_index=False).agg(shares_change=("shares_change","sum"), cash_proxy=("cash_proxy","sum"), etf_count=("code","nunique"))
    daily = daily.sort_values(["date","shares_change"], ascending=[True,False])
    daily["shares_change_5d"] = daily.groupby("industry")["shares_change"].transform(lambda s: s.rolling(5, min_periods=1).sum())
    daily["shares_change_20d"] = daily.groupby("industry")["shares_change"].transform(lambda s: s.rolling(20, min_periods=1).sum())
    df.to_csv(outdir / "etf_detail.csv", index=False, encoding="utf-8-sig")
    daily.to_csv(outdir / "industry_daily.csv", index=False, encoding="utf-8-sig")
    latest_date = daily["date"].max() if len(daily) else ""
    latest = daily[daily["date"] == latest_date].sort_values("shares_change", ascending=False)
    industries = sorted(daily["industry"].dropna().unique().tolist())
    chart_rows = daily.to_dict("records")
    table = latest.to_html(index=False, classes="data", float_format=lambda x: f"{x:,.2f}")
    detail = df.tail(200).to_html(index=False, classes="data", float_format=lambda x: f"{x:,.2f}")
    warnings = []
    if df["industry"].eq("未分类").any(): warnings.append(f"{int(df['industry'].eq('未分类').sum())} 行数据尚未完成行业映射")
    if df["shares"].le(0).any(): warnings.append("存在非正份额，请检查源文件单位")
    if duplicate_count: warnings.append(f"发现并移除 {duplicate_count} 条重复键")
    warning_html = "；".join(warnings) if warnings else "未发现基础质量问题"
    payload = json.dumps(chart_rows, ensure_ascii=False).replace("</", "<\\/")
    options = "<option value=''>全部行业</option>" + "".join(f"<option>{x}</option>" for x in industries)
    html = f'''<!doctype html><meta charset="utf-8"><title>国家队 ETF 份额跟踪</title>
<style>body{{font-family:-apple-system,BlinkMacSystemFont,"PingFang SC",sans-serif;margin:28px;color:#172033;background:#f6f8fb}}h1{{margin-bottom:4px}}.note,.quality{{padding:12px;background:#fff3cd;border-left:4px solid #e0a800}}.card{{background:#fff;padding:18px;margin:16px 0;border-radius:10px;box-shadow:0 2px 12px #0000000d;overflow:auto}}select{{padding:7px;margin-right:10px}}canvas{{width:100%;height:300px}}table{{border-collapse:collapse;width:100%;font-size:12px}}th,td{{padding:6px;border-bottom:1px solid #e8edf3;text-align:right;white-space:nowrap}}th{{background:#eef3f8}}th:first-child,td:first-child{{text-align:left}}</style>
<h1>国家队 ETF 份额跟踪看板</h1><p>最新日期：{latest_date}　样本行数：{len(df)}　ETF 数：{df['code'].nunique()}</p>
<div class="note">份额变化是 ETF 申赎与配置的代理指标，不等于国家队真实持仓；cash_proxy 仅为粗略估算，不构成投资建议。</div>
<div class="card"><h2>数据质量</h2><div class="quality">{warning_html}</div></div>
<div class="card"><h2>行业份额变化趋势</h2><select id="industry">{options}</select><select id="window"><option value="shares_change">单日变化</option><option value="shares_change_5d">5日累计变化</option><option value="shares_change_20d">20日累计变化</option></select><canvas id="chart" width="1000" height="300"></canvas></div>
<div class="card"><h2>最新交易日行业排名</h2>{table}</div><div class="card"><h2>ETF 明细（最近 200 行）</h2>{detail}</div>
<script>const rows={payload};const canvas=document.getElementById('chart'),ctx=canvas.getContext('2d');
function draw(){{const ind=document.getElementById('industry').value, key=document.getElementById('window').value;let a=rows.filter(x=>!ind||x.industry===ind);let dates=[...new Set(a.map(x=>x.date))].sort();let vals=dates.map(d=>a.filter(x=>x.date===d).reduce((s,x)=>s+(+x[key]||0),0));ctx.clearRect(0,0,canvas.width,canvas.height);if(!vals.length)return;let max=Math.max(...vals.map(Math.abs),1),w=canvas.width/(vals.length-1||1);ctx.strokeStyle='#1769aa';ctx.lineWidth=2;ctx.beginPath();vals.forEach((v,i)=>{{let x=i*w,y=150-v/max*120;i?ctx.lineTo(x,y):ctx.moveTo(x,y)}});ctx.stroke();ctx.fillStyle='#667085';ctx.font='12px sans-serif';ctx.fillText(dates[0],0,285);ctx.fillText(dates[dates.length-1],canvas.width-90,285);ctx.fillText('正值=份额增加',8,18)}}document.querySelectorAll('select').forEach(x=>x.onchange=draw);draw();</script>'''
    (outdir / "national_etf_dashboard.html").write_text(html, encoding="utf-8")
    print(f"生成: {outdir / 'national_etf_dashboard.html'}")

if __name__ == "__main__": main()
