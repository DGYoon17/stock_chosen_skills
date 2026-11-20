import importlib.util
import json
import sys
import unittest
from pathlib import Path


@unittest.skipUnless(importlib.util.find_spec("mcp"), "MCP SDK is optional")
class McpTests(unittest.IsolatedAsyncioTestCase):
    async def test_schema_and_round_trip(self):
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client

        root = Path(__file__).resolve().parents[1]
        params = StdioServerParameters(
            command=sys.executable,
            args=["-m", "stock_screening.mcp_server", "--data-dir", str(root / "examples" / "demo")],
            cwd=str(root),
        )
        async with stdio_client(params) as (incoming, outgoing):
            async with ClientSession(incoming, outgoing) as session:
                await session.initialize()
                tools = {tool.name: tool.inputSchema for tool in (await session.list_tools()).tools}

                screen = tools["screen_stock_liquidity"]
                self.assertEqual(set(screen["required"]), {"as_of", "min_avg_amount_cny"})
                self.assertEqual(screen["properties"]["window"]["type"], "integer")
                self.assertEqual(screen["properties"]["window"]["default"], 20)

                args = {"as_of": "2025-03-09", "min_avg_amount_cny": "100000000"}
                coverage = await session.call_tool("prepare_stock_data", {"as_of": args["as_of"]})
                self.assertFalse(coverage.isError, coverage.content)
                self.assertEqual(json.loads(coverage.content[0].text)["complete_count"], 3)
                result = await session.call_tool("screen_stock_liquidity", args)
                self.assertFalse(result.isError, result.content)
                report = json.loads(result.content[0].text)
                self.assertEqual(report["matches"][0]["symbol"], "990001.SH")
                check = await session.call_tool("verify_stock_screening", {**args, "report": report})
                self.assertFalse(check.isError, check.content)
                self.assertTrue(json.loads(check.content[0].text)["verified"])
