import ftplib
import os
import csv
import re
import json
from datetime import datetime
from pathlib import Path

REQUIRED_HEADERS = [
    "transaction_id", "timestamp", "store_id", "product_id",
    "quantity", "unit_price", "total_amount", "payment_method"
]

VALID_PAYMENT_METHODS = {"cash", "credit_card", "debit_card", "mobile_pay", "online"}
FILENAME_PATTERN = re.compile(r'^SALES_DATA_\d{14}\.csv$', re.IGNORECASE)

class CSVValidator:
    """Validates sales transaction CSV files against RRG business rules."""

    def __init__(self, error_log_manager):
        self.error_log = error_log_manager
        self.errors = []

    def validate_file(self, file_path):
        """Run all validation checks on a CSV file. Returns (is_valid, errors_list)."""
        self.errors = []
        filename = os.path.basename(file_path)

        # 1. Filename format validation
        if not self._validate_filename(filename):
            return False, self.errors

        # 2. File not empty
        if os.path.getsize(file_path) == 0:
            self._add_error(filename, "EMPTY_FILE", "File is 0 bytes (empty).")
            return False, self.errors

        # 3. Try to parse CSV
        try:
            with open(file_path, 'r', newline='', encoding='utf-8') as f:
                reader = csv.reader(f)
                rows = list(reader)
        except Exception as e:
            self._add_error(filename, "MALFORMED_CSV", f"Cannot parse CSV: {str(e)}")
            return False, self.errors

        if not rows:
            self._add_error(filename, "EMPTY_CONTENT", "CSV has no rows.")
            return False, self.errors

        # 4. Header validation
        headers = [h.strip().strip('"').lower() for h in rows[0]]
        if not self._validate_headers(filename, headers):
            return False, self.errors

        # 5. Row-level validation
        data_rows = rows[1:]
        if not self._validate_data_rows(filename, headers, data_rows):
            return False, self.errors

        return True, []

    def _validate_filename(self, filename):
        if not FILENAME_PATTERN.match(filename):
            self._add_error(
                filename, 
                "INVALID_FILENAME", 
                f"Filename '{filename}' does not match pattern SALE_DATA_YYYYMMDDHHMMSS.csv"
            )
            return False
        return True

    def _validate_headers(self, filename, headers):
        missing = [h for h in REQUIRED_HEADERS if h not in headers]
        if missing:
            self._add_error(
                filename,
                "INVALID_HEADERS",
                f"Missing or incorrect headers. Expected: {REQUIRED_HEADERS}. Missing: {missing}. Found: {headers}"
            )
            return False
        return True

    def _validate_data_rows(self, filename, headers, data_rows):
        valid = True
        transaction_ids = set()

        for idx, row in enumerate(data_rows, start=2):
            # Check column count
            if len(row) != len(REQUIRED_HEADERS):
                self._add_error(
                    filename,
                    "MISSING_COLUMNS",
                    f"Row {idx}: Expected {len(REQUIRED_HEADERS)} columns, found {len(row)}. Data: {row}"
                )
                valid = False
                continue

            # Build row dict
            row_dict = {}
            for i, header in enumerate(REQUIRED_HEADERS):
                row_dict[header] = row[i].strip().strip('"')

            # transaction_id uniqueness
            tid = row_dict.get("transaction_id", "")
            if tid in transaction_ids:
                self._add_error(
                    filename,
                    "DUPLICATE_TRANSACTION_ID",
                    f"Row {idx}: Duplicate transaction_id '{tid}' within file."
                )
                valid = False
            transaction_ids.add(tid)

            # Numeric validations
            try:
                qty = float(row_dict["quantity"])
                price = float(row_dict["unit_price"])
                total = float(row_dict["total_amount"])

                if qty <= 0:
                    self._add_error(filename, "INVALID_QUANTITY", f"Row {idx}: quantity={qty} must be positive.")
                    valid = False

                if price <= 0:
                    self._add_error(filename, "INVALID_PRICE", f"Row {idx}: unit_price={price} must be positive.")
                    valid = False

                if total <= 0:
                    self._add_error(filename, "INVALID_TOTAL", f"Row {idx}: total_amount={total} must be positive.")
                    valid = False

                # Check total = qty * price (allow small floating point tolerance)
                expected_total = round(qty * price, 2)
                actual_total = round(total, 2)
                if abs(expected_total - actual_total) > 0.01:
                    self._add_error(
                        filename,
                        "INCORRECT_TOTAL",
                        f"Row {idx}: total_amount={total} does not equal quantity*unit_price={expected_total}."
                    )
                    valid = False

            except ValueError as e:
                self._add_error(filename, "INVALID_NUMERIC", f"Row {idx}: Non-numeric value in numeric field. {e}")
                valid = False

            # Timestamp validation
            ts = row_dict.get("timestamp", "")
            if not self._is_valid_timestamp(ts):
                self._add_error(filename, "INVALID_TIMESTAMP", f"Row {idx}: Invalid timestamp '{ts}'.")
                valid = False

            # Payment method validation
            pm = row_dict.get("payment_method", "").lower().strip()
            if pm not in VALID_PAYMENT_METHODS:
                self._add_error(
                    filename,
                    "INVALID_PAYMENT_METHOD",
                    f"Row {idx}: Invalid payment_method '{pm}'. Valid: {VALID_PAYMENT_METHODS}"
                )
                valid = False

        return valid

    def _is_valid_timestamp(self, ts):
        """Check if timestamp is valid datetime format."""
        formats = [
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d %H:%M",
            "%Y-%m-%d"
        ]
        for fmt in formats:
            try:
                datetime.strptime(ts, fmt)
                return True
            except ValueError:
                continue
        return False

    def _add_error(self, filename, error_type, details):
        self.errors.append({"type": error_type, "details": details})
        self.error_log.add_entry(filename, error_type, details)


