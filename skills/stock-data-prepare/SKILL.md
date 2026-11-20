---
name: stock-data-prepare
description: 检查 A 股筛选所需的交易日历、基准日股票池和日成交额，确认指定窗口的数据覆盖情况。适用于准备选股输入或排查覆盖、缺失和重复行情问题。
---

# 准备选股数据

确认数据目录、基准日期 `as_of` 和回看交易日数 `window`。基准日和窗口应来自用户请求或明确的策略版本。对真实行情，基准日应落在已完成数据采集的日期范围内。

- 已连接本项目的 MCP 服务时，调用 `prepare_stock_data(as_of, window)` 检查服务所绑定的数据目录。
- 使用本地文件时，在项目根目录运行 `python -m stock_screening prepare --data-dir <目录> --as-of <YYYY-MM-DD> --window <交易日数>`。需要了解输入字段或准备新数据时，阅读 [CSV 数据约定](references/data-contract.md)。

把实际交易日范围、完整和缺失的股票数量、`snapshot_sha256` 交给筛选步骤。若出现日历覆盖不足或重复行，引用工具返回的错误定位数据。缺数的个股交由筛选工具按缺失规则处理。
