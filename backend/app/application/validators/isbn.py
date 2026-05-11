from __future__ import annotations

from typing import Annotated

from pydantic import AfterValidator


def validate_isbn13(isbn: str) -> str:
    """
    Return True if isbn is a valid ISBN-13 (13 digits, correct checksum).
    https://bestbookshub.com/isbn-check-digit-calculator/
    """
    digits = isbn.replace("-", "").replace(" ", "")
    if len(digits) != 13 or not digits.isdigit():
        raise ValueError("ISBN-13 must be 13 numeric digits (dashes/spaces allowed)")

    total = sum(int(d) * (1 if i % 2 == 0 else 3) for i, d in enumerate(digits[:12]))
    check = (10 - (total % 10)) % 10
    if check != int(digits[12]):
        raise ValueError("Invalid ISBN-13 checksum")

    return digits


Isbn13Str = Annotated[
    str,
    AfterValidator(validate_isbn13),
]
