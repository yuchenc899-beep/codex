"""
Data Validation Helpers
Schema, range, and completeness validation for tracker data.
"""

from datetime import datetime
from typing import Any


def validate_trade_schema(trade: dict, required_keys: list[str]) -> tuple[bool, str]:
    """
    Validate trade dict has all required keys with non-None values.

    Args:
        trade: Trade dictionary to validate
        required_keys: List of required key names

    Returns:
        (is_valid, error_message)
    """
    for key in required_keys:
        if key not in trade:
            return False, f"Missing key: {key}"
        if trade[key] is None:
            return False, f"None value for key: {key}"
    return True, "OK"


def validate_date_range(
    date_str: str, min_date: str = "2020-01-01"
) -> tuple[bool, str]:
    """
    Validate date is within reasonable range.

    Args:
        date_str: Date string in YYYY-MM-DD format
        min_date: Minimum allowed date (default: 2020-01-01)

    Returns:
        (is_valid, error_message)
    """
    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        min_obj = datetime.strptime(min_date, "%Y-%m-%d")
        if date_obj < min_obj:
            return False, f"Date too old: {date_str} (min: {min_date})"
        if date_obj > datetime.now():
            return False, f"Date in future: {date_str}"
        return True, "OK"
    except ValueError as e:
        return False, f"Invalid date format: {date_str} ({e})"


def validate_positive_values(trade: dict, value_keys: list[str]) -> tuple[bool, str]:
    """
    Validate numeric values are non-negative.

    Args:
        trade: Trade dictionary to validate
        value_keys: List of keys that should have non-negative numeric values

    Returns:
        (is_valid, error_message)
    """
    for key in value_keys:
        if key in trade and isinstance(trade[key], (int, float)):
            if trade[key] < 0:
                return False, f"Negative value for {key}: {trade[key]}"
    return True, "OK"


def assert_complete_keys(data: dict, required_keys: list[str]) -> bool:
    """
    Assert all required keys present (for use in tests).

    Args:
        data: Dictionary to check
        required_keys: List of required key names

    Returns:
        True if all keys present

    Raises:
        AssertionError: If any keys are missing
    """
    missing = [k for k in required_keys if k not in data]
    if missing:
        raise AssertionError(f"Missing keys: {missing}")
    return True


def validate_trade_complete(trade: dict) -> tuple[bool, str]:
    """
    Comprehensive validation of a trade dict.
    Checks schema, date range, and value ranges.

    Args:
        trade: Trade dictionary to validate

    Returns:
        (is_valid, error_message)
    """
    # Schema validation
    required_keys = ["name", "ticker", "transaction_date"]
    valid, msg = validate_trade_schema(trade, required_keys)
    if not valid:
        return valid, msg

    # Date validation (if present and not empty)
    if trade.get("transaction_date"):
        valid, msg = validate_date_range(trade["transaction_date"])
        if not valid:
            return valid, msg

    # Value validation (if numeric fields present)
    value_keys = ["purchases", "sales", "total"]
    valid, msg = validate_positive_values(trade, value_keys)
    if not valid:
        return valid, msg

    return True, "OK"


def validate_congress_trade(trade: dict) -> tuple[bool, str]:
    """
    Validate a congress trade dict (from congress.py normalize_trade).

    Args:
        trade: Congress trade dictionary

    Returns:
        (is_valid, error_message)
    """
    required_keys = [
        "ticker",
        "name",
        "chamber",
        "party",
        "type",
        "transaction_date",
    ]
    return validate_trade_schema(trade, required_keys)


def validate_house_reps_trade(trade: dict) -> tuple[bool, str]:
    """
    Validate a House Reps trade dict (from house_reps.py normalize_house_fd_trade).

    Args:
        trade: House Reps trade dictionary

    Returns:
        (is_valid, error_message)
    """
    required_keys = [
        "name",
        "chamber",
        "transaction_date",
    ]
    return validate_trade_schema(trade, required_keys)


def validate_sec13f_holding(holding: dict) -> tuple[bool, str]:
    """
    Validate a SEC 13F holding dict.

    Args:
        holding: Holding dictionary

    Returns:
        (is_valid, error_message)
    """
    required_keys = ["name", "value", "shares"]
    valid, msg = validate_trade_schema(holding, required_keys)
    if not valid:
        return valid, msg

    # Validate value and shares are non-negative
    value_keys = ["value", "shares"]
    return validate_positive_values(holding, value_keys)
