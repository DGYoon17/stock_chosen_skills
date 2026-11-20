---
name: stock-liquidity-screen
description: 按指定基准日、交易日窗口和日均成交额门槛筛选 A 股。适用于将流动性或近期成交活跃度要求转换为可复现的股票清单。
---

# 按日均成交额筛选

确认 `as_of`、`window` 和人民币元门槛 `min_avg_amount_cny`。将「1 亿元」换算为字符串 `"100000000"`。当前策略采用「严格超过」。若用户明确要求其他比较方式或指标，先说明当前实现支持的策略范围。

- 已连接本项目的 MCP 服务时，调用 `screen_stock_liquidity(as_of, min_avg_amount_cny, window)`。本地运行 `python -m stock_screening screen --data-dir <目录> --as-of <YYYY-MM-DD> --window <交易日数> --min-avg-amount-cny <元> --output <结果.json>`。
- 采用工具返回的 `matches` 和 `incomplete`，分别汇报入选股及行情缺失的排除项。日均成交额按完整交易日窗口计算，显示值保留两位小数。以报告中的 `data.sessions` 为准标注日期范围。
- 保留完整 JSON 报告以便复核。需要核对结果时，运行 `stock-result-check` Skill，并传入原先的筛选参数。
