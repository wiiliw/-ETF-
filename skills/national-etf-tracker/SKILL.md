---
name: national-etf-tracker
description: "国家队 ETF 份额跟踪与行业资金流向看板：采集沪市 ETF 日基金份额，导入深市交易所历史文件，维护 ETF-行业映射，计算份额变化和粗略资金代理指标，输出 CSV 与离线 HTML 看板。只要用户提到国家队、ETF 份额、沪深 ETF 资金流向、行业 ETF 申赎、ETF 跟踪看板或想从份额变化观察大资金配置，就使用本 skill。"
compatibility: "Python 3.10+; pandas; 可选 akshare、openpyxl。"
---

# 国家队 ETF 跟踪

## 目标与边界
用 ETF 基金份额变化观察指数化资金的配置方向。份额变化是申赎代理，不是国家队真实持仓披露；输出中始终保留该免责声明。不要把价格上涨造成的规模变化误判为净申购。

## 标准工作流
1. 先读取本 skill 的 `config/industry_mapping.csv`，确认分类是否覆盖当前 ETF；不能确定时放入“未分类”，不要凭名称猜行业。
2. 采集或导入原始数据，保留原文件在 `data/raw/`，使用 `scripts/merge_sources.py` 合并并写入 `data/processed/etf_shares.csv`，同时生成质量报告。
3. 执行聚合脚本，生成 `data/processed/industry_daily.csv` 和 `output/national_etf_dashboard.html`。
4. 检查数据日期、重复键、缺失份额和异常跳变；把数据源、下载时间、文件名写入说明或终端日志。

## 数据源
### 沪市
使用 `scripts/collect_sse_akshare.py`。当前 AKShare 1.18.x 的实测接口是 `fund_etf_scale_sse(date="YYYYMMDD")`，返回 `基金代码、基金简称、统计日期、基金份额`；脚本会逐交易日调用并转换为标准字段。可用 `--raw-dir` 保存每日原始响应，便于审计。接口会随版本变化，字段不匹配时应停止并提示用户升级/确认，而不是静默生成错误数据。

### 深市
优先使用 `scripts/collect_szse_akshare.py` 调用 `fund_scale_daily_szse(start_date, end_date, symbol="ETF")`。单次区间不得超过约 6 个月，因此历史数据应拆成多个区间；当前 AKShare 建议至少使用 1.18.52。若接口不可用，再把交易所按半年下载的 CSV/XLS/XLSX/TSV 文件放入 `data/raw/shenzhen/`，执行 `scripts/import_shenzhen.py --input-dir data/raw/shenzhen`。支持常见列名：日期/交易日期、证券代码/基金代码、证券简称/基金简称、基金份额/份额、收盘价/收盘价(元)。导入时统一市场为 `SZ`，并保留 `source_file`。

## 标准字段
`date, source, market, code, name, shares, share_unit, close, industry, source_file`

- `shares`：份额，统一为“份”；交易所接口已按其返回口径处理，不重复乘万。
- `share_unit`：固定为 `份`，用于防止跨源合并时发生单位误读。
- `close`：可选收盘价；没有价格时保留空值。
- `industry`：来自映射 CSV；缺失为“未分类”。

## 核心指标
- ETF 日份额变化：`shares - shares.shift(1)`。
- ETF 日份额变化率：`shares_change / previous_shares`。
- 行业份额变化：行业内 ETF 日份额变化求和。
- 粗略资金代理：`shares_change * previous_close`；仅在价格口径和份额单位可比时使用。
- 5/20 日累计变化：按行业对日变化滚动求和。

看板至少展示：最新日期、沪/深数据覆盖、行业份额变化排名、近 5/20 日变化、ETF 明细、数据质量警告。

## 年度批量抓取
先按年份执行沪市整年采集，深市按上下半年拆分；也可以直接使用批处理器：
```bash
python skills/national-etf-tracker/scripts/collect_years.py \
  --start-year 2024 \
  --end-date 2026-08-22
```
批处理器会将年度原始文件保存到 `data/raw/annual/`，合并结果写入 `data/processed/etf_shares.csv`，并生成 `quality_report.json`。如需断点重跑，可删除失败年份的输出文件后重新执行。

## 命令示例
```bash
python skills/national-etf-tracker/scripts/import_shenzhen.py \
  --input-dir skills/national-etf-tracker/data/raw/shenzhen
python skills/national-etf-tracker/scripts/collect_sse_akshare.py \
  --start-date 2024-01-01 --end-date 2024-12-31 \
  --output skills/national-etf-tracker/data/raw/sse_akshare.csv
python skills/national-etf-tracker/scripts/merge_sources.py \
  --inputs skills/national-etf-tracker/data/raw/sse.csv skills/national-etf-tracker/data/raw/szse.csv \
  --output skills/national-etf-tracker/data/processed/etf_shares.csv \
  --report skills/national-etf-tracker/data/processed/quality_report.json
python skills/national-etf-tracker/scripts/build_dashboard.py \
  --input skills/national-etf-tracker/data/processed/etf_shares.csv \
  --mapping skills/national-etf-tracker/config/industry_mapping.csv \
  --output-dir skills/national-etf-tracker/output
```

若只想用已有统一 CSV，可直接运行最后一个命令；脚本会自动写行业汇总 CSV。

## GitHub 大文件分片
`data/processed/etf_shares.csv` 和 `output/etf_detail.csv` 体积较大，仓库使用分片目录保存：
- `data/processed/etf_shares_parts/etf_shares.part-*.csv`
- `output/etf_detail_parts/etf_detail.part-*.csv`

需要恢复完整 CSV 时：
```bash
python skills/national-etf-tracker/scripts/split_csv.py merge \
  --parts-glob 'skills/national-etf-tracker/data/processed/etf_shares_parts/*.csv' \
  --output skills/national-etf-tracker/data/processed/etf_shares.csv
python skills/national-etf-tracker/scripts/split_csv.py merge \
  --parts-glob 'skills/national-etf-tracker/output/etf_detail_parts/*.csv' \
  --output skills/national-etf-tracker/output/etf_detail.csv
```


## 解释注意
- 单日份额大增可能来自联接基金、做市、套利或数据修订，不等于单日买入。
- 不同数据源的披露时点、单位、复权和代码格式可能不同，先做质量检查再比较。
- 该工具是研究看板，不构成投资建议。
