"""Expose stock-screening tools over MCP stdio with one configured data bundle."""

import argparse
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from .liquidity import screen_liquidity, verify_result
from .market import load_snapshot


def create_server(data_dir: Path) -> FastMCP:
    server = FastMCP("stock-screening")

    @server.tool()
    def prepare_stock_data(as_of: str, window: int = 20) -> dict:
        """Check the configured bundle for a YYYY-MM-DD cutoff and trailing session count."""
        return load_snapshot(data_dir, as_of, window).summary()

    @server.tool()
    def screen_stock_liquidity(as_of: str, min_avg_amount_cny: str, window: int = 20) -> dict:
        """Return stocks with mean daily turnover strictly above a decimal threshold in CNY."""
        snapshot = load_snapshot(data_dir, as_of, window)
        return screen_liquidity(snapshot, min_avg_amount_cny)

    @server.tool()
    def verify_stock_screening(as_of: str, min_avg_amount_cny: str, report: dict, window: int = 20) -> dict:
        """Recompute a full screening report using the original cutoff, threshold and window."""
        snapshot = load_snapshot(data_dir, as_of, window)
        return verify_result(snapshot, min_avg_amount_cny, report)

    return server


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", required=True, type=Path)
    args = parser.parse_args()
    create_server(args.data_dir.resolve()).run(transport="stdio")


if __name__ == "__main__":
    main()
