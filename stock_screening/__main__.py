"""Command-line entry point for preparing, screening and checking a bundle."""

import argparse
import csv
import json
import os
import sys
from pathlib import Path
from tempfile import NamedTemporaryFile

from .liquidity import screen_liquidity, verify_result
from .market import DATA_FILES, load_snapshot


def arguments(argv):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for command, help_text in (
        ("prepare", "validate the bundle and report coverage"),
        ("screen", "select stocks above the average-turnover threshold"),
        ("verify", "recompute a screening report and check for differences"),
    ):
        subparser = commands.add_parser(command, help=help_text)
        subparser.add_argument("--data-dir", required=True, type=Path)
        subparser.add_argument("--as-of", required=True, help="last calendar date to consider, YYYY-MM-DD")
        subparser.add_argument("--window", type=int, default=20, help="number of open sessions (default 20)")
        subparser.add_argument("--output", type=Path, help="write UTF-8 JSON to a file")
        if command != "prepare":
            subparser.add_argument("--min-avg-amount-cny", required=True)
        if command == "verify":
            subparser.add_argument("--report", type=Path, required=True)
    return parser.parse_args(argv)


def save_json(path: Path, result: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = None
    try:
        with NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent, delete=False) as stream:
            temporary_path = Path(stream.name)
            json.dump(result, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
        os.replace(temporary_path, path)
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def main(argv=None) -> int:
    args = arguments(argv)
    try:
        inputs = {(args.data_dir / name).resolve() for name in DATA_FILES}
        if args.command == "verify":
            inputs.add(args.report.resolve())
        if args.output is not None and args.output.resolve() in inputs:
            raise ValueError("output path must be different from the input files")

        snapshot = load_snapshot(args.data_dir, args.as_of, args.window)
        if args.command == "prepare":
            result = snapshot.summary()
        elif args.command == "screen":
            result = screen_liquidity(snapshot, args.min_avg_amount_cny)
        else:
            with args.report.open(encoding="utf-8-sig") as stream:
                report = json.load(stream)
            result = verify_result(snapshot, args.min_avg_amount_cny, report)

        if args.output is None:
            print(json.dumps(result, indent=2))
        else:
            save_json(args.output, result)
        return 0 if result.get("verified", True) else 1
    except (ValueError, OSError, csv.Error) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
