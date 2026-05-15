"""Unit tests for ORM model instantiation and enum values."""

import datetime as dt

from app.db.models.loan import LoanStatus


def test_loan_status_enum_values() -> None:
    """LoanStatus enum must have exactly the three expected values."""
    assert set(LoanStatus) == {LoanStatus.ACTIVE, LoanStatus.RETURNED, LoanStatus.OVERDUE}


def test_loan_status_string_values() -> None:
    """LoanStatus values must match the DB ENUM strings."""
    assert LoanStatus.ACTIVE.value == "ACTIVE"
    assert LoanStatus.RETURNED.value == "RETURNED"
    assert LoanStatus.OVERDUE.value == "OVERDUE"


def test_loan_status_is_str() -> None:
    """LoanStatus inherits str so it serialises correctly."""
    assert isinstance(LoanStatus.ACTIVE, str)


def test_utc_alias_available() -> None:
    """datetime.UTC must be available (Python 3.11+)."""
    now = dt.datetime.now(dt.UTC)
    assert now.tzinfo is not None
