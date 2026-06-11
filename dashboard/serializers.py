"""Helpers to convert asyncpg/DB types into JSON-safe values."""
import datetime
from decimal import Decimal


def serialize(val):
    if val is None:
        return None
    if isinstance(val, Decimal):
        return float(val)
    if isinstance(val, datetime.time):
        return val.strftime("%H:%M")
    if isinstance(val, datetime.datetime):
        return val.isoformat()
    if isinstance(val, datetime.date):
        return val.isoformat()
    if isinstance(val, datetime.timedelta):
        return str(val)
    return val


def row(record) -> dict:
    return {k: serialize(v) for k, v in dict(record).items()}


def rows(records) -> list:
    return [row(r) for r in records]
