# test_csv_validator.py

import pytest
from filevalidation import CSVValidator


# -----------------------------
# Dummy Error Log Manager
# -----------------------------
class DummyErrorLog:
    def __init__(self):
        self.logs = []

    def add_entry(self, filename, error_type, details):
        self.logs.append({
            "filename": filename,
            "error_type": error_type,
            "details": details
        })


# -----------------------------
# Fixtures
# -----------------------------
@pytest.fixture
def error_log():
    return DummyErrorLog()


@pytest.fixture
def validator(error_log):
    return CSVValidator(error_log)


@pytest.fixture
def valid_csv(tmp_path):
    csv_file = tmp_path / "SALES_DATA_20260721153045.csv"

    csv_file.write_text(
        """transaction_id,timestamp,store_id,product_id,quantity,unit_price,total_amount,payment_method
TX001,2026-07-21 10:30:00,S001,P001,2,10,20,cash
""",
        encoding="utf-8"
    )

    return csv_file


@pytest.fixture
def empty_csv(tmp_path):
    csv_file = tmp_path / "SALES_DATA_20260721153045.csv"
    csv_file.write_text("", encoding="utf-8")
    return csv_file


@pytest.fixture
def invalid_filename_csv(tmp_path):
    csv_file = tmp_path / "sales.csv"

    csv_file.write_text(
        """transaction_id,timestamp,store_id,product_id,quantity,unit_price,total_amount,payment_method
TX001,2026-07-21 10:30:00,S001,P001,2,10,20,cash
""",
        encoding="utf-8"
    )

    return csv_file


@pytest.fixture
def missing_header_csv(tmp_path):
    csv_file = tmp_path / "SALES_DATA_20260721153045.csv"

    csv_file.write_text(
        """transaction_id,timestamp,store_id,product_id,quantity,unit_price,total_amount
TX001,2026-07-21 10:30:00,S001,P001,2,10,20
""",
        encoding="utf-8"
    )

    return csv_file


@pytest.fixture
def duplicate_transaction_csv(tmp_path):
    csv_file = tmp_path / "SALES_DATA_20260721153045.csv"

    csv_file.write_text(
        """transaction_id,timestamp,store_id,product_id,quantity,unit_price,total_amount,payment_method
TX001,2026-07-21 10:30:00,S001,P001,2,10,20,cash
TX001,2026-07-21 11:00:00,S001,P002,1,30,30,cash
""",
        encoding="utf-8"
    )

    return csv_file


@pytest.fixture
def invalid_payment_csv(tmp_path):
    csv_file = tmp_path / "SALES_DATA_20260721153045.csv"

    csv_file.write_text(
        """transaction_id,timestamp,store_id,product_id,quantity,unit_price,total_amount,payment_method
TX001,2026-07-21 10:30:00,S001,P001,2,10,20,bitcoin
""",
        encoding="utf-8"
    )

    return csv_file


# -----------------------------
# Test Cases
# -----------------------------

def test_valid_csv(validator, valid_csv):
    result, errors = validator.validate_file(valid_csv)

    assert result is True
    assert errors == []


def test_empty_file(validator, empty_csv):
    result, errors = validator.validate_file(empty_csv)

    assert result is False
    assert errors[0]["type"] == "EMPTY_FILE"


def test_invalid_filename(validator, invalid_filename_csv):
    result, errors = validator.validate_file(invalid_filename_csv)

    assert result is False
    assert errors[0]["type"] == "INVALID_FILENAME"


def test_missing_headers(validator, missing_header_csv):
    result, errors = validator.validate_file(missing_header_csv)

    assert result is False
    assert errors[0]["type"] == "INVALID_HEADERS"


def test_duplicate_transaction_id(validator, duplicate_transaction_csv):
    result, errors = validator.validate_file(duplicate_transaction_csv)

    assert result is False

    assert any(
        error["type"] == "DUPLICATE_TRANSACTION_ID"
        for error in errors
    )


def test_invalid_payment_method(validator, invalid_payment_csv):
    result, errors = validator.validate_file(invalid_payment_csv)

    assert result is False

    assert any(
        error["type"] == "INVALID_PAYMENT_METHOD"
        for error in errors
    )