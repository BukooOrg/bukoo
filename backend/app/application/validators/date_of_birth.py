from datetime import date
from typing import Annotated

from pydantic import AfterValidator


def validate_date_of_birth(value: date) -> date:
    from datetime import date as date_type

    today = date_type.today()
    if value >= today:
        raise ValueError("date_of_birth must be in the past.")
    age_years = (
        today.year - value.year - ((today.month, today.day) < (value.month, value.day))
    )
    if age_years < 5:
        raise ValueError("User must be at least 5 years old.")
    return value


DateOfBirth = Annotated[date, AfterValidator(validate_date_of_birth)]
