from typing import Annotated

from pydantic import AfterValidator, Field


def validate_otp(value: str) -> str:
    if not value.isdigit() or len(value) != 6:
        raise ValueError("OTP must be a 6-digit numeric string.")
    return value


OTPStr = Annotated[
    str,
    Field(min_length=1, max_length=6),
    AfterValidator(validate_otp),
]
