from datetime import datetime, timezone


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def elapsed_ms(start: datetime, end: datetime) -> int:
    return int((end - start).total_seconds() * 1000)
