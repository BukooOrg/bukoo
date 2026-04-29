from datetime import UTC


def _utc(dt: object) -> object:
    """Attach UTC timezone to a naive datetime returned by the DB driver."""
    from datetime import datetime

    if isinstance(dt, datetime) and dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt
