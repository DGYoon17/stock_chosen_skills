---
name: stock-result-check
description: 用同一基准日、窗口、门槛和源行情重新计算选股报告，核查数据版本、入选名单、金额和排除项。适用于交付前复核或排查两次筛选结果的差异。
---

# 核验选股结果

取得完整原始报告以及用户当时确认的 `as_of`、窗口和金额门槛。使用生成报告时的数据目录或 MCP 服务绑定目录。

- 通过 MCP 调用 `verify_stock_screening(as_of, min_avg_amount_cny, report, window)`，或者在项目根目录运行 `python -m stock_screening verify --data-dir <目录> --as-of <YYYY-MM-DD> --window <交易日数> --min-avg-amount-cny <元> --report <结果.json>`。
- `verified` 为真时，说明提交的报告与重新计算的结果一致。为假时，引用 `mismatched_fields` 并定位差异。若 `data` 有差异，先比对日期窗口、股票池和行情指纹。若 `matches` 或 `incomplete` 有差异，检查入选名单、金额和缺失日期。
