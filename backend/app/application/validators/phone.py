import re
from typing import Annotated

from pydantic import AfterValidator, Field

# Matching Examples
# - standard International: +60123456789
# - formatted with Spaces: +1 (555) 123-4567
# - local with Dashes: 012-345 6789
# - dotted Format: 123.456.7890
# - shortest valid (5 chars): 12345
_PHONE_RE = re.compile(r"^\+?[\d\s\-().]{5,20}$")


def validate_phone_number(v: str) -> str:
    v = v.strip()
    if not v:
        raise ValueError("phone must not be blank")
    if not _PHONE_RE.match(v):
        raise ValueError(
            "phone must contain only digits, spaces, hyphens, parentheses, "
            "dots, and an optional leading '+'"
        )
    return v


PhoneNumber = Annotated[
    str, Field(min_length=5, max_length=20), AfterValidator(validate_phone_number)
]
