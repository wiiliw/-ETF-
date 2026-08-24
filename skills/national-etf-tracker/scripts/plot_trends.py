#!/usr/bin/env python3
"""Plot broad ETF balance proxy and readable Jun-Aug 2026 industry trends."""
from __future__ import annotations
import argparse, math
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

COLORS = {'科技':'#2563EB','医药医疗':'#DC2626','金融':'#7C3AED','新能源':'#16A34A','消费':'#EA580C','军工':'#475569','资源周期':'#92400E','汽车':'#0891B2','农业':'#65A30D','地产基建':'#A16207','高端制造':'#4F46E5','公用事业':'#DB2777'}
RULES = [('科技',['半导体','芯片','软件','计算机','人工智能','AI','通信','电子','大数据','云计算','机器人','信创','互联网','传媒']),('医药医疗',['医药','医疗','创新药','生物','中药','疫苗']),('金融',['证券','券商','银行','保险','金融']),('新能源',['新能源','光伏','储能','电池','锂电','风电','清洁能源']),('消费',['消费','酒','食品','饮料','旅游','家电','零售','餐饮','养殖']),('军工',['军工','国防','航空航天']),('资源周期',['有色','煤炭','钢铁','化工','石油','油气','稀土','黄金','资源','材料']),('汽车',['汽车','智能车','新能源车']),('农业',['农业','畜牧','粮食','种业']),('地产基建',['地产','房地产','基建','建筑建材']),('高端制造',['机械','机床','工业母机','高端装备','智能制造']),('公用事业',['电力','水务','公用事业','环保'])]
EXCLUDE_WORDS=['红利','低波','价值','成长','现金流','债券增强']
FIXED_GROUPS=[('债券/货币',['债','货币','现金']),('商品',['黄金','商品','豆粕','有色金属期货']),('港股/海外',['纳指','标普','恒生','港股','港股通','H股','日经','德国','法国','沙特','东南亚','MSCI','海外','全球']),('区域主题',['粤港澳','大湾区','长三角','雄安','京津冀','国企改革','央企'])]
BROAD_WORDS=['沪深300','中证500','中证1000','中证2000','中证A50','上证50','创业板','科创50','科创100','双创50','科创创业','科创板50','A50','A500','深证100','深主板50','国证2000','上证180','中证800','中证全指','中证红利']

def auto_industry(name: str, explicit: str | None) -> str:
    if explicit == '宽基指数': return '宽基/综合指数'
    if explicit and explicit not in {'未分类','海外指数','红利策略'}: return explicit
    text=str(name)
    if any(x in text for x in BROAD_WORDS): return '宽基/综合指数'
    for group, words in FIXED_GROUPS:
        if any(x.lower() in text.lower() for x in words): return group
    if any(x in text for x in EXCLUDE_WORDS): return '策略类'
    for industry, words in RULES:
        if any(x.lower() in text.lower() for x in words): return industry
    return '待人工确认'

def main() -> None:
    ap=argparse.ArgumentParser(); ap.add_argument('--input',required=True); ap.add_argument('--mapping',required=True); ap.add_argument('--output-dir',required=True); ap.add_argument('--industry-start',default='2026-06-01'); ap.add_argument('--industry-end',default=None); args=ap.parse_args()
    out=Path(args.output_dir); out.mkdir(parents=True,exist_ok=True)
    d=pd.read_csv(args.input,dtype={'code':str}); m=pd.read_csv(args.mapping,dtype={'code':str})
    d=d.drop(columns=['industry'],errors='ignore').merge(m[['code','industry']],on='code',how='left'); d['date']=pd.to_datetime(d.date); d=d.sort_values(['market','code','date'])
    latest_names=d.sort_values('date').groupby(['market','code'],as_index=False).tail(1)[['market','code','name','industry']]
    latest_names['plot_industry']=[auto_industry(n,i if pd.notna(i) else None) for n,i in zip(latest_names.name,latest_names.industry)]
    latest_names['classification_rule']=latest_names.apply(lambda r:'人工映射' if pd.notna(r.industry) and r.industry not in {'未分类','宽基指数','海外指数','红利策略'} else ('宽基关键词/人工映射' if r.plot_industry=='宽基/综合指数' else ('固定类别/排除词' if r.plot_industry in {'非行业/策略','债券/货币','商品','港股/海外','区域主题','策略类'} else '名称关键词')),axis=1)
    latest_names.to_csv(out/'industry_classification_auto.csv',index=False,encoding='utf-8-sig')
    d=d.merge(latest_names[['market','code','plot_industry']],on=['market','code'],how='left'); d['share_change']=d.groupby(['market','code']).shares.diff()
    broad=d[d.plot_industry.eq('宽基/综合指数')]; broad_daily=broad.groupby('date',as_index=False).shares.sum().rename(columns={'shares':'estimated_balance_shares'}); broad_daily['estimated_balance_100m_shares']=broad_daily.estimated_balance_shares/1e8; base=broad_daily.estimated_balance_shares.iloc[0]; broad_daily['balance_index_2024_01_02']=broad_daily.estimated_balance_shares/base; broad_daily.to_csv(out/'broad_estimated_balance_2024_to_present.csv',index=False,encoding='utf-8-sig')
    end=pd.Timestamp(args.industry_end) if args.industry_end else d.date.max(); start=pd.Timestamp(args.industry_start); x=d[(d.date>=start)&(d.date<=end)&d.plot_industry.isin(COLORS)].copy()
    balances=x.groupby(['date','plot_industry'],as_index=False).shares.sum(); first=balances.groupby('plot_industry').shares.first(); balances['change_pct_from_start']=balances.apply(lambda r:(r.shares/first[r.plot_industry]-1)*100,axis=1); balances.to_csv(out/'industry_trend_2026_06_07_08.csv',index=False,encoding='utf-8-sig')
    membership=latest_names[latest_names.plot_industry.isin(COLORS)].copy(); membership['颜色']=membership.plot_industry.map(COLORS); membership=membership.rename(columns={'market':'市场','code':'ETF代码','name':'ETF名称','plot_industry':'衡量行业','classification_rule':'分类依据'}); membership[['衡量行业','颜色','市场','ETF代码','ETF名称','分类依据']].sort_values(['衡量行业','市场','ETF代码']).to_csv(out/'industry_etf_membership_2026.csv',index=False,encoding='utf-8-sig')
    plt.rcParams['font.sans-serif']=['PingFang SC','Arial Unicode MS','DejaVu Sans']; plt.rcParams['axes.unicode_minus']=False
    fig,ax=plt.subplots(figsize=(16,8),dpi=160); ax.plot(broad_daily.date,broad_daily.estimated_balance_100m_shares,color='#B42318',linewidth=2); ax.grid(alpha=.25); ax.set_title('宽基 ETF 总份额余额代理（2024年至今）'); ax.set_ylabel('余额（亿份）'); fig.tight_layout(); fig.savefig(out/'broad_estimated_balance_2024_to_present.png',bbox_inches='tight'); plt.close(fig)
    industries=sorted(balances.plot_industry.unique()); cols=3; rows=math.ceil(len(industries)/cols); fig,axes=plt.subplots(rows,cols,figsize=(16,3.7*rows),dpi=160,sharex=True); axes=list(getattr(axes,'flat',[axes]))
    for ax,industry in zip(axes,industries):
        s=balances[balances.plot_industry.eq(industry)]; color=COLORS[industry]; ax.plot(s.date,s.change_pct_from_start,color=color,linewidth=2); ax.fill_between(s.date,s.change_pct_from_start,0,color=color,alpha=.12); ax.axhline(0,color='#999',linewidth=.7); ax.set_title(f'{industry}  ·  {color}',color=color,fontweight='bold'); ax.set_ylabel('较6月初余额变化 (%)'); ax.grid(alpha=.22)
    for ax in axes[len(industries):]: ax.axis('off')
    fig.suptitle('行业 ETF 余额趋势（2026年6—8月；未分类、宽基及非行业策略已排除）',fontsize=16); fig.tight_layout(rect=(0,0,1,.97)); fig.savefig(out/'industry_trend_2026_06_07_08.png',bbox_inches='tight'); plt.close(fig)
    counts=latest_names.plot_industry.value_counts(); classified=int(counts.reindex(COLORS.keys(),fill_value=0).sum()); summary=pd.DataFrame({'行业':industries,'颜色':[COLORS[i] for i in industries],'ETF数量':[int(counts.get(i,0)) for i in industries]}); legend=summary.to_html(index=False,classes='data'); membership_html=membership.to_html(index=False,index_names=False,classes='data')
    html=f'''<!doctype html><meta charset="utf-8"><title>ETF余额与行业趋势</title><style>body{{font-family:Arial,"PingFang SC";margin:30px;background:#f6f8fb}}.card{{background:#fff;padding:20px;margin:16px 0;border-radius:10px;overflow:auto}}img{{max-width:100%}}table{{border-collapse:collapse;font-size:12px;width:100%}}td,th{{padding:7px 10px;border-bottom:1px solid #ddd;white-space:nowrap;text-align:left}}th{{background:#eef3f8}}.note{{background:#fff3cd;padding:12px}}</style><h1>ETF余额与行业趋势</h1><div class="note">行业趋势按“衡量行业”聚合。每个行业使用的 ETF 清单见下方明细表及 industry_etf_membership_2026.csv；颜色固定，未分类、宽基、海外及策略 ETF 不进入行业图。当前行业样本 ETF 数：{classified}。</div><div class="card"><h2>行业颜色与样本数</h2>{legend}</div><div class="card"><h2>行业趋势（2026年6—8月）</h2><img src="industry_trend_2026_06_07_08.png"></div><div class="card"><h2>行业对应 ETF 明细</h2>{membership_html}</div><div class="card"><h2>宽基余额代理（2024年至今）</h2><img src="broad_estimated_balance_2024_to_present.png"></div>'''; (out/'trend_charts_balance_industry_2026.html').write_text(html,encoding='utf-8'); print('generated',out/'trend_charts_balance_industry_2026.html')
if __name__=='__main__': main()
