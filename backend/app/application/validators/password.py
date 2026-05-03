import re

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
