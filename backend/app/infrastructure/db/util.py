from uuid_extension import uuid7


def uuid7_str() -> str:
    """Generate a UUID v7 string. Time-sortable, index-friendly."""
    return str(uuid7())
