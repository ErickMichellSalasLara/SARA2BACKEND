from __future__ import annotations

from datetime import date, datetime, time
from decimal import Decimal
from typing import Any, Iterable, Mapping


def json_value(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, time):
        return value.strftime("%H:%M:%S")
    if isinstance(value, Decimal):
        return float(value)
    return value


def row_to_dict(row: Mapping[str, Any]) -> dict[str, Any]:
    return {key: json_value(value) for key, value in row.items()}


def rows_to_dicts(rows: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return [row_to_dict(row) for row in rows]
