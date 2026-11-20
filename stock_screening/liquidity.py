"""Screen a fixed universe by trailing mean daily turnover in CNY."""

import json
from decimal import Decimal, ROUND_HALF_UP

from .market import Snapshot, parse_amount_cents


STRATEGY = "mean-daily-turnover/v1"


def screen_liquidity(snapshot: Snapshot, min_avg_amount_cny: str) -> dict:
    threshold = parse_amount_cents(min_avg_amount_cny)
    days = len(snapshot.sessions)
    matches = []
    incomplete = []
    for symbol, name in sorted(snapshot.universe.items()):
        amounts = snapshot.available_amounts(symbol)
        if len(amounts) < days:
            missing_dates = [day.isoformat() for day in snapshot.sessions if day not in amounts]
            incomplete.append({"symbol": symbol, "name": name, "missing_dates": missing_dates})
            continue

        total_cents = sum(amounts.values())
        if total_cents > threshold * days:
            average = (Decimal(total_cents) / (days * 100)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            matches.append((total_cents, {"symbol": symbol, "name": name, "avg_amount_cny": str(average)}))

    matches.sort(key=lambda item: (-item[0], item[1]["symbol"]))
    return {
        "strategy": STRATEGY,
        "window": days,
        "min_avg_amount_cny": f"{Decimal(threshold) / 100:.2f}",
        "comparison": ">",
        "data": snapshot.summary(),
        "matches": [row for _, row in matches],
        "incomplete": incomplete,
        "below_or_equal_count": len(snapshot.universe) - len(matches) - len(incomplete),
    }


def verify_result(snapshot: Snapshot, min_avg_amount_cny: str, report: dict) -> dict:
    if not isinstance(report, dict):
        raise ValueError("report must be a JSON object")
    expected = screen_liquidity(snapshot, min_avg_amount_cny)
    differences = []
    for field in sorted(expected.keys() | report.keys()):
        if field not in expected or field not in report:
            differences.append(field)
            continue
        if json.dumps(expected[field], sort_keys=True) != json.dumps(report[field], sort_keys=True):
            differences.append(field)
    return {"verified": not differences, "mismatched_fields": differences, "snapshot_sha256": expected["data"]["snapshot_sha256"]}
