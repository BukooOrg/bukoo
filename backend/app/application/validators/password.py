import re
from typing import Annotated

from pydantic import AfterValidator, Field

UPPER_RE = re.compile(r"[A-Z]")
LOWER_RE = re.compile(r"[a-z]")
DIGIT_RE = re.compile(r"\d")
SPECIAL_RE = re.compile(r"[^\w\s]")  # any non-alphanumeric, non-space

# common weak passwords blacklist
COMMON_PASSWORDS = {
    "password",
    "password123",
    "12345678",
    "qwerty123",
    "admin123",
}


def validate_password(value: str) -> str:
    if not UPPER_RE.search(value):
        raise ValueError("Password must contain at least one uppercase letter.")
    if not LOWER_RE.search(value):
        raise ValueError("Password must contain at least one lowercase letter.")
    if not DIGIT_RE.search(value):
        raise ValueError("Password must contain at least one digit.")
    if not SPECIAL_RE.search(value):
        raise ValueError("Password must contain at least one special character.")

    # weak password checks
    lowered = value.lower()

    if lowered in COMMON_PASSWORDS:
        raise ValueError("Password is too common.")
    if "password" in lowered:
        raise ValueError("Password must not contain the word 'password'.")

    # prevent repeated characters like "aaaaaaaA1!"
    if len(set(value)) < 4:
        raise ValueError("Password is too simple or repetitive.")

    # prevent sequences like "12345678" or "abcdefg"
    if value.isdigit() or value.isalpha():
        raise ValueError("Password must mix different character types.")

    return value


PasswordStr = Annotated[
    str,
    Field(min_length=8, max_length=128),
    AfterValidator(validate_password),
]
