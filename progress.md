# Progress

- AKShare 已升级到 1.18.88。
- 已按年份/季度/月度分段采集真实 ETF 份额：2024 全年、2025 全年、2026-01-01 至 2026-08-22；沪深市场均覆盖到最新有效数据日 2026-08-21。
- 已采集并合并 744,443 行：SH 427,285 行，SZ 317,158 行，1,644 个 ETF 代码。
- 已生成 `data/processed/etf_shares.csv`、`quality_report.json` 和 `output/national_etf_dashboard.html`。
- 新增 `scripts/plot_trends.py`，生成 2024 年至今宽基和已映射行业的 5 日滚动份额变化折线图，以及 HTML 图表页。
- 图表验证通过：日度趋势数据 639 个有效日期，覆盖 2024-01-02 至 2026-08-21；PNG 和 HTML 文件均存在。
