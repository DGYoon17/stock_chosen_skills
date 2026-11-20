# A 股流动性筛选 Skills

用自然语言给出基准日、回看窗口和成交额门槛，Agent 通过 Skill 选择工具。Python 根据交易日历和行情计算，保留可复核的筛选报告。示例数据和证券代码均为合成数据。

## 三个 Skill

| Skill | 什么时候用 | 输出 |
| --- | --- | --- |
| [`stock-data-prepare`](skills/stock-data-prepare/SKILL.md) | 准备数据或排查缺失 | 交易日范围、覆盖数量、数据指纹 |
| [`stock-liquidity-screen`](skills/stock-liquidity-screen/SKILL.md) | 筛选日均成交额严格超过门槛的股票 | 入选清单、日均成交额、缺数排除项 |
| [`stock-result-check`](skills/stock-result-check/SKILL.md) | 复核报告或定位结果差异 | 是否通过、差异字段、重算数据指纹 |

## 离线运行

在仓库根目录用 Python 3.10 或更高版本运行。以下命令只使用标准库，无需账号和 API Key。

```sh
python -m stock_screening prepare --data-dir examples/demo --as-of 2025-03-09
python -m stock_screening screen --data-dir examples/demo --as-of 2025-03-09 --min-avg-amount-cny 100000000 --output outputs/demo-report.json
python -m stock_screening verify --data-dir examples/demo --as-of 2025-03-09 --min-avg-amount-cny 100000000 --report outputs/demo-report.json
```

默认窗口为 20 个交易日。这个样例应入选 `990001.SH`，日均成交额为 `130000000.00` 元。`990002.SH` 恰好等于门槛，`990003.SZ` 缺少 2 月 26 日行情，`990004.BJ` 低于门槛。复核返回 `"verified": true`。

替换 `--data-dir` 即可使用自己的数据。字段和单位要求见 [CSV 数据约定](skills/stock-data-prepare/references/data-contract.md)。筛选使用精确金额比较，显示值四舍五入到分。复核使用同一套规则重算，报告差异时退出码为 `1`，输入错误时为 `2`。

## 接入 Agent

把仓库的 `skills/` 设为 Agent 的 Skill 来源。运行命令的工作目录设为仓库根目录。一个可交给 Agent 的任务是「用合成样例，按 2025-03-09 为基准筛选最近 20 个交易日日均成交额严格超过 1 亿元的股票，并复核完整报告」。

如使用 MCP，在客户端配置以下 stdio 启动命令。服务启动时绑定数据目录。

```sh
python -m pip install "mcp>=1.12,<2"
python -m stock_screening.mcp_server --data-dir examples/demo
```

FastMCP 从工具函数签名生成 `inputSchema`。例如 `screen_stock_liquidity` 的 `window: int = 20` 会导出整数类型和默认值 `20`。CLI 和 MCP 共用相同的计算逻辑。

## 测试与公开发布

```sh
python -m unittest discover -s tests -v
```

基础测试覆盖样例结果、缺数、重复行情、窗口不足和报告篡改。安装 MCP SDK 后，同一命令也会测试 stdio 工具列表和实际调用。

公开发布时，使用合成演示数据，确认发布者有权公开代码，并选定许可证。接入真实数据源时，独立确认其再分发许可，把访问凭证留在本地配置中。
