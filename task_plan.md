# 国家队 ETF 跟踪数据看板

## Goal
创建一个可复用的 skill：采集沪深 ETF 日基金份额，维护历史数据，按行业聚合并生成国家队资金流向观察看板。数据只用于跟踪与研究，不把份额变化直接等同于国家队真实持仓。

## Phases

### Phase 1: 安装与审查 planning-with-files
**Status:** complete
- [x] 克隆指定 GitHub 仓库
- [x] 阅读主 SKILL.md、reference.md 和脚本红旗
- [x] 安装到用户 skill 目录

### Phase 2: 设计 ETF 看板 skill
**Status:** complete
- [x] 确定目录、输入输出和数据模型
- [x] 写 SKILL.md 与配置模板

### Phase 3: 实现采集与分析脚本
**Status:** complete
- [x] 实现沪市 AKShare 采集
- [x] 实现深圳 AKShare 区间采集与手动历史文件导入
- [x] 实现清洗、去重、行业聚合和指标计算
- [x] 实现 HTML 看板输出

### Phase 4: 验证与交付
**Status:** complete
- [x] 用模拟数据跑通端到端流程
- [x] 做 Python 语法检查
- [x] 整理安装、使用和数据口径说明

## Decisions Made
- 份额变化是 ETF 资金申赎的代理指标，不直接宣称等于国家队真实持仓。
- 沪市优先使用 AKShare；深市允许把交易所历史下载文件放入 raw 目录后统一导入。
- 行业分类单独维护 mapping.csv，避免把基金名称关键词当成可靠分类。
- 输出同时保留明细 CSV、行业日汇总 CSV 和离线 HTML 看板。

## Errors Encountered
| Error | Attempt | Resolution |
|---|---:|---|
| 当前目录没有项目文件 | 1 | 从空目录建立 skill 与脚本结构 |

## Next Step
年度数据已覆盖至当前日期，继续补充行业映射与看板指标。
