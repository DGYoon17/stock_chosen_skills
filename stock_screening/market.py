"""Read and validate the data needed for one screening date."""

import csv
import hashlib
import json
import re
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from pathlib import Path


DATA_FILES = ("calendar.csv", "universe.csv", "quotes.csv")
AMOUNT_PATTERN = re.compile(r"[0-9]{1,15}(?:\.[0-9]{1,2})?")
SYMBOL_PATTERN = re.compile(r"[0-9]{6}\.(?:SH|SZ|BJ)")


def parse_date(value: str) -> date:
    parsed = date.fromisoformat(value)
    if parsed.isoformat() != value:
        raise ValueError(f"expected YYYY-MM-DD, got {value!r}")
    return parsed


def parse_amount_cents(value: str) -> int:
    if not AMOUNT_PATTERN.fullmatch(value):
        raise ValueError(f"expected a nonnegative CNY amount with up to two decimals, got {value!r}")
    return int(Decimal(value) * 100)


def read_rows(path: Path, columns: tuple[str, ...]):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream, strict=True)
        headers = reader.fieldnames or []
        if len(headers) != len(set(headers)) or not set(columns).issubset(headers):
            raise ValueError(f"{path.name} needs unique headers including {', '.join(columns)}")
        for row in reader:
            if None in row or any(value is None for value in row.values()):
                raise ValueError(f"{path.name}:{reader.line_num}: wrong number of columns")
            yield reader.line_num, {name: row[name].strip() for name in columns}


@dataclass(frozen=True)
class Snapshot:
    as_of: date
    sessions: tuple[date, ...]
    universe: dict[str, str]
    amounts: dict[tuple[str, date], int]

    def available_amounts(self, symbol: str) -> dict[date, int]:
        return {day: self.amounts[symbol, day] for day in self.sessions if (symbol, day) in self.amounts}

    def summary(self) -> dict:
        members = sorted(self.universe.items())
        quotes = sorted((symbol, day.isoformat(), amount) for (symbol, day), amount in self.amounts.items())
        session_dates = [day.isoformat() for day in self.sessions]
        contents = json.dumps([session_dates, members, quotes], separators=(",", ":"))
        complete_count = sum(len(self.available_amounts(symbol)) == len(self.sessions) for symbol in self.universe)
        return {
            "as_of": self.as_of.isoformat(),
            "sessions": session_dates,
            "snapshot_sha256": hashlib.sha256(contents.encode("utf-8")).hexdigest(),
            "universe_count": len(members),
            "complete_count": complete_count,
            "incomplete_count": len(members) - complete_count,
        }


def load_snapshot(data_dir: Path, as_of: str, window: int = 20) -> Snapshot:
    if type(window) is not int or window < 1:
        raise ValueError("window must be a positive integer")
    cutoff = parse_date(as_of)
    calendar_path, universe_path, quotes_path = (data_dir / name for name in DATA_FILES)

    calendar = {}
    for line, row in read_rows(calendar_path, ("date", "is_open")):
        day = parse_date(row["date"])
        if day in calendar or row["is_open"] not in {"0", "1"}:
            raise ValueError(f"{calendar_path.name}:{line}: duplicate date or invalid is_open")
        calendar[day] = row["is_open"] == "1"
    if cutoff not in calendar:
        raise ValueError(f"calendar.csv does not cover as_of {as_of}")
    dates = sorted(day for day in calendar if day <= cutoff)
    if (cutoff - dates[0]).days + 1 != len(dates):
        raise ValueError("calendar.csv has missing dates on or before as_of")
    sessions = tuple(day for day in dates if calendar[day])[-window:]
    if len(sessions) != window:
        raise ValueError(f"calendar.csv provides {len(sessions)} open sessions, need {window}")

    universe = {}
    for line, row in read_rows(universe_path, ("symbol", "name")):
        symbol = row["symbol"]
        if not SYMBOL_PATTERN.fullmatch(symbol) or not row["name"] or symbol in universe:
            raise ValueError(f"{universe_path.name}:{line}: invalid or duplicate symbol, or missing name")
        universe[symbol] = row["name"]
    if not universe:
        raise ValueError("universe.csv must contain at least one symbol")

    session_set = set(sessions)
    amounts = {}
    for line, row in read_rows(quotes_path, ("symbol", "trade_date", "amount_cny")):
        symbol = row["symbol"]
        day = parse_date(row["trade_date"])
        if day not in session_set or symbol not in universe:
            continue
        key = (symbol, day)
        if key in amounts:
            raise ValueError(f"{quotes_path.name}:{line}: duplicate quote for {symbol} on {day}")
        try:
            amounts[key] = parse_amount_cents(row["amount_cny"])
        except ValueError as error:
            raise ValueError(f"{quotes_path.name}:{line}: {error}") from error

    return Snapshot(cutoff, sessions, universe, amounts)
