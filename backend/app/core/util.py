from __future__ import annotations

from datetime import UTC


def size_to_bytes(size: int | float | str) -> int | None:
    """
    Convert a human-readable size string (KB, MB, GB, TB) or number to bytes.
    Supports binary units (1 KB = 1024 bytes).
    """
    units = {"b": 1, "kb": 1024, "mb": 1024**2, "gb": 1024**2, "tb": 1024**2}

    try:
        if isinstance(size, int | float):
            return int(size)

        if not isinstance(size, str):
            raise ValueError("Input must be a string or a number.")

        size = size.strip().lower()
        num_str = "".join(ch for ch in size if ch.isdigit() or ch == ".")
        unit_str = "".join(ch for ch in size if ch.isalpha())

        if not num_str:
            raise ValueError("No numeric value found.")

        value = float(num_str)

        if not unit_str:
            raise ValueError(
                f"Unknown unit '{unit_str}'. Supported: {', '.join(units.keys())}"
            )

        return int(value * units[unit_str])

    except ValueError as e:
        print(f"Error: {e}")
        return None


def _utc(dt: object) -> object:
    """Attach UTC timezone to a naive datetime returned by the DB driver."""
    from datetime import datetime

    if isinstance(dt, datetime) and dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt
