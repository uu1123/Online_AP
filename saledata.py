"""
Sales Data Validation & Archival System

"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import ftplib
import os
import csv
import re
import json
import hashlib
import shutil
from datetime import datetime
from pathlib import Path
import threading
import requests
import uuid


# ============================================================================
# CONFIGURATION
# ============================================================================
APP_TITLE = "Sales Data Validation System"
WINDOW_WIDTH = 1000
WINDOW_HEIGHT = 700

REQUIRED_HEADERS = [
    "transaction_id", "timestamp", "store_id", "product_id",
    "quantity", "unit_price", "total_amount", "payment_method"
]

VALID_PAYMENT_METHODS = {"cash", "credit_card", "debit_card", "mobile_pay", "online"}

FILENAME_PATTERN = re.compile(r'^SALES_DATA_\d{14}\.csv$', re.IGNORECASE)

# External API for UUID generation (fallback to uuid module if offline)
UUID_API_URL = "https://www.uuidtools.com/api/generate/v1"


# ============================================================================
# ERROR LOG MODEL - Uses UUID for each entry (via API or local fallback)
# ============================================================================
class ErrorLogEntry:
    """Represents a single error log entry with a unique UUID."""

    def __init__(self, filename, error_type, error_details, timestamp=None):
        self.uuid = self._generate_uuid()
        self.filename = filename
        self.error_type = error_type
        self.error_details = error_details
        self.timestamp = timestamp or datetime.now().isoformat()

    def _generate_uuid(self):
        """Generate UUID using external API, fallback to uuid module."""
        try:
            response = requests.get(UUID_API_URL, timeout=5)
            if response.status_code == 200:
                api_uuid = response.text.strip().strip('"')
                if self._is_valid_uuid(api_uuid):
                    return api_uuid
        except Exception:
            pass
        # Fallback to Python's uuid module
        return str(uuid.uuid4())

    @staticmethod
    def _is_valid_uuid(val):
        """Validate UUID format."""
        try:
            uuid.UUID(val)
            return True
        except ValueError:
            return False

    def to_dict(self):
        return {
            "uuid": self.uuid,
            "timestamp": self.timestamp,
            "filename": self.filename,
            "error_type": self.error_type,
            "error_details": self.error_details
        }

    def to_log_string(self):
        return f"[{self.timestamp}] UUID: {self.uuid} | File: {self.filename} | Type: {self.error_type} | Details: {self.error_details}"


class ErrorLogManager:
    """Manages error log entries with UUID tracking."""

    def __init__(self, log_file_path="error_log.json"):
        self.log_file_path = log_file_path
        self.entries = []
        self._load_existing()

    def _load_existing(self):
        if os.path.exists(self.log_file_path):
            try:
                with open(self.log_file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.entries = data.get("entries", [])
            except Exception:
                self.entries = []

    def add_entry(self, filename, error_type, error_details):
        entry = ErrorLogEntry(filename, error_type, error_details)
        self.entries.append(entry.to_dict())
        self._save()
        return entry.uuid

    def _save(self):
        data = {
            "log_metadata": {
                "application": APP_TITLE,
                "generated_at": datetime.now().isoformat(),
                "total_entries": len(self.entries)
            },
            "entries": self.entries
        }
        os.makedirs(os.path.dirname(self.log_file_path) if os.path.dirname(self.log_file_path) else '.', exist_ok=True)
        with open(self.log_file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)

    def get_entries(self):
        return self.entries

    def clear(self):
        self.entries = []
        self._save()


# ============================================================================
# CSV VALIDATION ENGINE
# ============================================================================
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


# ============================================================================
# FILE TRACKING & ARCHIVAL
# ============================================================================
class FileTracker:
    """Tracks processed files to prevent duplicates using SHA-256 hashing."""

    def __init__(self, tracker_file="processed_files.json"):
        self.tracker_file = tracker_file
        self.processed_hashes = set()
        self._load()

    def _load(self):
        if os.path.exists(self.tracker_file):
            try:
                with open(self.tracker_file, 'r') as f:
                    data = json.load(f)
                    self.processed_hashes = set(data.get("hashes", []))
            except Exception:
                self.processed_hashes = set()

    def _save(self):
        with open(self.tracker_file, 'w') as f:
            json.dump({"hashes": list(self.processed_hashes)}, f)

    def compute_hash(self, file_path):
        sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                sha256.update(chunk)
        return sha256.hexdigest()

    def is_processed(self, file_path):
        file_hash = self.compute_hash(file_path)
        return file_hash in self.processed_hashes

    def mark_processed(self, file_path):
        file_hash = self.compute_hash(file_path)
        self.processed_hashes.add(file_hash)
        self._save()


class ArchiveManager:
    """Manages archival of valid files into date-based directory structure."""

    def __init__(self, archive_dir):
        self.archive_dir = archive_dir

    def archive_file(self, file_path, filename):
        """Archive file into YYYY/MM/DD directory structure based on filename timestamp."""
        # Extract timestamp from filename: SALE_DATA_YYYYMMDDHHMMSS.csv
        match = re.search(r'SALE_DATA_(\d{4})(\d{2})(\d{2})(\d{2})(\d{2})(\d{2})', filename, re.IGNORECASE)
        if match:
            year, month, day, hour, minute, second = match.groups()
            subdir = os.path.join(year, month, day)
        else:
            now = datetime.now()
            subdir = os.path.join(str(now.year), f"{now.month:02d}", f"{now.day:02d}")

        dest_dir = os.path.join(self.archive_dir, subdir)
        os.makedirs(dest_dir, exist_ok=True)
        dest_path = os.path.join(dest_dir, filename)

        # Handle duplicate filenames in archive
        counter = 1
        base_dest = dest_path
        while os.path.exists(dest_path):
            name, ext = os.path.splitext(base_dest)
            dest_path = f"{name}_{counter}{ext}"
            counter += 1

        shutil.copy2(file_path, dest_path)
        return dest_path


# ============================================================================
# FTP CLIENT
# ============================================================================
class FTPClient:
    """Handles FTP connection and file operations."""

    def __init__(self):
        self.ftp = None
        self.connected = False
        self.host = None
        self.username = None

    def connect(self, host, username, password, port=21):
        try:
            self.ftp = ftplib.FTP()
            self.ftp.connect(host, port, timeout=10)
            self.ftp.login(username, password)
            self.connected = True
            self.host = host
            self.username = username
            return True, "Connected successfully."
        except Exception as e:
            self.connected = False
            return False, f"Connection failed: {str(e)}"

    def disconnect(self):
        if self.ftp:
            try:
                self.ftp.quit()
            except Exception:
                pass
        self.connected = False
        self.ftp = None
        return True, "Disconnected."

    def list_files(self, directory="."):
        if not self.connected or not self.ftp:
            return []
        try:
            files = []
            self.ftp.cwd(directory)
            self.ftp.retrlines('LIST', files.append)
            return files
        except Exception as e:
            return [f"Error: {str(e)}"]

    def get_file_list(self, directory="."):
        if not self.connected or not self.ftp:
            return []
        try:
            self.ftp.cwd(directory)
            return self.ftp.nlst()
        except Exception:
            return []

    def download_file(self, remote_filename, local_path):
        if not self.connected or not self.ftp:
            return False, "Not connected."
        try:
            with open(local_path, 'wb') as f:
                self.ftp.retrbinary(f'RETR {remote_filename}', f.write)
            return True, f"Downloaded {remote_filename}"
        except Exception as e:
            return False, f"Download failed: {str(e)}"


# ============================================================================
# MAIN GUI APPLICATION
# ============================================================================
class SaleDataApp:
    """Main GUI application matching the provided interface design."""

    def __init__(self, root):
        self.root = root
        self.root.title(APP_TITLE)
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.root.configure(bg='#e0e0e0')
        self.root.resizable(True, True)

        # Initialize backend components
        self.ftp_client = FTPClient()
        self.error_log = ErrorLogManager("error_log.json")
        self.validator = CSVValidator(self.error_log)
        self.file_tracker = FileTracker()
        self.archive_manager = None

        # Variables
        self.download_dir = tk.StringVar()
        self.archive_dir = tk.StringVar()
        self.errors_dir = tk.StringVar(value=".")
        self.ftp_host = tk.StringVar(value="127.0.0.1")
        self.ftp_username = tk.StringVar()
        self.ftp_password = tk.StringVar()
        self.filter_text = tk.StringVar()
        self.connection_status = tk.StringVar(value="Disconnected")

        self.server_files = []
        self.selected_file = None

        self._build_ui()

    def _build_ui(self):
        # Main container with padding
        main_frame = tk.Frame(self.root, bg='#e0e0e0')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Title bar
        title_frame = tk.Frame(main_frame, bg='#e0e0e0')
        title_frame.pack(fill=tk.X, pady=(0, 10))

        title_label = tk.Label(
            title_frame, 
            text="SALE DATA VALIDATION SYSTEM",
            font=('Arial', 14, 'bold'),
            bg='#e0e0e0',
            fg='black'
        )
        title_label.pack(side=tk.LEFT)

        self.status_label = tk.Label(
            title_frame,
            textvariable=self.connection_status,
            font=('Arial', 10),
            bg='#e0e0e0',
            fg='red'
        )
        self.status_label.pack(side=tk.RIGHT)

        # Three-column layout
        columns_frame = tk.Frame(main_frame, bg='#e0e0e0')
        columns_frame.pack(fill=tk.BOTH, expand=True)

        # Configure grid weights
        columns_frame.columnconfigure(0, weight=1)
        columns_frame.columnconfigure(1, weight=2)
        columns_frame.columnconfigure(2, weight=3)
        columns_frame.rowconfigure(0, weight=1)

        # === COLUMN 1: Connection ===
        conn_frame = tk.LabelFrame(
            columns_frame,
            text="Connection",
            font=('Arial', 10, 'bold'),
            bg='#d4d4d4',
            fg='black',
            bd=2,
            relief=tk.GROOVE
        )
        conn_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5), pady=5)

        # FTP Host
        tk.Label(conn_frame, text="FTP Host", bg='#d4d4d4', font=('Arial', 9)).pack(anchor=tk.W, padx=5, pady=(5, 0))
        host_entry = tk.Entry(conn_frame, textvariable=self.ftp_host, font=('Arial', 9))
        host_entry.pack(fill=tk.X, padx=5, pady=2)

        # Username
        tk.Label(conn_frame, text="Username", bg='#d4d4d4', font=('Arial', 9)).pack(anchor=tk.W, padx=5, pady=(5, 0))
        user_entry = tk.Entry(conn_frame, textvariable=self.ftp_username, font=('Arial', 9))
        user_entry.pack(fill=tk.X, padx=5, pady=2)

        # Password
        tk.Label(conn_frame, text="Password", bg='#d4d4d4', font=('Arial', 9)).pack(anchor=tk.W, padx=5, pady=(5, 0))
        pass_entry = tk.Entry(conn_frame, textvariable=self.ftp_password, show="*", font=('Arial', 9))
        pass_entry.pack(fill=tk.X, padx=5, pady=2)

        # Buttons
        btn_frame = tk.Frame(conn_frame, bg='#d4d4d4')
        btn_frame.pack(fill=tk.X, padx=5, pady=10)

        self.connect_btn = tk.Button(
            btn_frame, text="Connect", command=self._connect_ftp,
            width=10, font=('Arial', 9)
        )
        self.connect_btn.pack(side=tk.LEFT, padx=(0, 5))

        self.disconnect_btn = tk.Button(
            btn_frame, text="Disconnect", command=self._disconnect_ftp,
            width=10, font=('Arial', 9), state=tk.DISABLED
        )
        self.disconnect_btn.pack(side=tk.LEFT)

        # === COLUMN 2: Server Browser ===
        browser_frame = tk.LabelFrame(
            columns_frame,
            text="Server Browser",
            font=('Arial', 10, 'bold'),
            bg='#d4d4d4',
            fg='black',
            bd=2,
            relief=tk.GROOVE
        )
        browser_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)

        # Filter row
        filter_frame = tk.Frame(browser_frame, bg='#d4d4d4')
        filter_frame.pack(fill=tk.X, padx=5, pady=5)

        tk.Label(filter_frame, text="Filter:", bg='#d4d4d4', font=('Arial', 9)).pack(side=tk.LEFT)
        filter_entry = tk.Entry(filter_frame, textvariable=self.filter_text, font=('Arial', 9), width=15)
        filter_entry.pack(side=tk.LEFT, padx=5)

        tk.Button(filter_frame, text="Apply", command=self._apply_filter, font=('Arial', 8), width=6).pack(side=tk.LEFT, padx=2)
        tk.Button(filter_frame, text="Res", command=self._reset_filter, font=('Arial', 8), width=4).pack(side=tk.LEFT, padx=2)

        # File list
        list_frame = tk.Frame(browser_frame, bg='#d4d4d4')
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.file_listbox = tk.Listbox(
            list_frame,
            yscrollcommand=scrollbar.set,
            font=('Courier New', 9),
            bg='white',
            selectmode=tk.SINGLE
        )
        self.file_listbox.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.file_listbox.yview)

        self.file_listbox.bind('<<ListboxSelect>>', self._on_file_select)

        # === COLUMN 3: Workspace & Actions ===
        workspace_frame = tk.LabelFrame(
            columns_frame,
            text="Workspace & Actions",
            font=('Arial', 10, 'bold'),
            bg='#d4d4d4',
            fg='black',
            bd=2,
            relief=tk.GROOVE
        )
        workspace_frame.grid(row=0, column=2, sticky="nsew", padx=(5, 0), pady=5)

        # Directory fields
        dir_configs = [
            ("Download directory", self.download_dir),
            ("Archive directory", self.archive_dir),
            ("Errors directory", self.errors_dir)
        ]

        for label_text, var in dir_configs:
            row = tk.Frame(workspace_frame, bg='#d4d4d4')
            row.pack(fill=tk.X, padx=5, pady=3)

            tk.Label(row, text=label_text, bg='#d4d4d4', font=('Arial', 9), anchor=tk.W).pack(fill=tk.X)

            entry_row = tk.Frame(row, bg='#d4d4d4')
            entry_row.pack(fill=tk.X, pady=2)

            entry = tk.Entry(entry_row, textvariable=var, font=('Arial', 9))
            entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

            tk.Button(
                entry_row, text="Browse...", 
                command=lambda v=var: self._browse_directory(v),
                font=('Arial', 8), width=8
            ).pack(side=tk.RIGHT, padx=(5, 0))

        # Action buttons
        action_frame = tk.Frame(workspace_frame, bg='#d4d4d4')
        action_frame.pack(fill=tk.X, padx=5, pady=10)

        self.validate_btn = tk.Button(
            action_frame, text="Validate Selected File",
            command=self._validate_selected,
            font=('Arial', 9), state=tk.DISABLED, width=20
        )
        self.validate_btn.pack(fill=tk.X, pady=2)

        self.process_btn = tk.Button(
            action_frame, text="Process Selected File",
            command=self._process_selected,
            font=('Arial', 9), state=tk.DISABLED, width=20
        )
        self.process_btn.pack(fill=tk.X, pady=2)

        btn_row2 = tk.Frame(action_frame, bg='#d4d4d4')
        btn_row2.pack(fill=tk.X, pady=2)

        tk.Button(btn_row2, text="Open Error Log", command=self._open_error_log, font=('Arial', 9), width=15).pack(side=tk.LEFT, fill=tk.X, expand=True)
        tk.Button(btn_row2, text="Clear Activity Feed", command=self._clear_activity, font=('Arial', 9), width=15).pack(side=tk.RIGHT, fill=tk.X, expand=True)

        # === ACTIVITY FEED ===
        activity_frame = tk.LabelFrame(
            main_frame,
            text="Activity Feed",
            font=('Arial', 10, 'bold'),
            bg='#d4d4d4',
            fg='black',
            bd=2,
            relief=tk.GROOVE
        )
        activity_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))

        self.activity_text = scrolledtext.ScrolledText(
            activity_frame,
            wrap=tk.WORD,
            font=('Courier New', 9),
            bg='white',
            state=tk.DISABLED
        )
        self.activity_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Initial message
        self._log_activity("Sale Data Console initialized.")
        self._log_activity("Ready for connection. Please configure FTP settings.")

    # === EVENT HANDLERS ===

    def _connect_ftp(self):
        host = self.ftp_host.get().strip()
        username = self.ftp_username.get().strip()
        password = self.ftp_password.get()

        if not host:
            messagebox.showerror("Error", "FTP Host is required.")
            return

        self._log_activity(f"Connecting to {host}...")

        success, msg = self.ftp_client.connect(host, username or "anonymous", password or "")

        if success:
            self.connection_status.set("Connected")
            self.status_label.config(fg='green')
            self.connect_btn.config(state=tk.DISABLED)
            self.disconnect_btn.config(state=tk.NORMAL)
            self._log_activity(msg)
            self._refresh_file_list()
        else:
            self._log_activity(f"ERROR: {msg}")
            messagebox.showerror("Connection Failed", msg)

    def _disconnect_ftp(self):
        success, msg = self.ftp_client.disconnect()
        self.connection_status.set("Disconnected")
        self.status_label.config(fg='red')
        self.connect_btn.config(state=tk.NORMAL)
        self.disconnect_btn.config(state=tk.DISABLED)
        self.file_listbox.delete(0, tk.END)
        self._log_activity(msg)

    def _refresh_file_list(self):
        self.file_listbox.delete(0, tk.END)
        if not self.ftp_client.connected:
            return

        files = self.ftp_client.get_file_list()
        self.server_files = [f for f in files if f.lower().endswith('.csv')]

        for f in self.server_files:
            self.file_listbox.insert(tk.END, f)

        self._log_activity(f"Found {len(self.server_files)} CSV files on server.")

    def _apply_filter(self):
        filter_str = self.filter_text.get().lower()
        self.file_listbox.delete(0, tk.END)

        for f in self.server_files:
            if filter_str in f.lower():
                self.file_listbox.insert(tk.END, f)

        self._log_activity(f"Filter applied: '{filter_str}' - {self.file_listbox.size()} results.")

    def _reset_filter(self):
        self.filter_text.set("")
        self.file_listbox.delete(0, tk.END)
        for f in self.server_files:
            self.file_listbox.insert(tk.END, f)
        self._log_activity("Filter reset.")

    def _on_file_select(self, event):
        selection = self.file_listbox.curselection()
        if selection:
            self.selected_file = self.file_listbox.get(selection[0])
            self.validate_btn.config(state=tk.NORMAL)
            self.process_btn.config(state=tk.NORMAL)
            self._log_activity(f"Selected file: {self.selected_file}")
        else:
            self.selected_file = None
            self.validate_btn.config(state=tk.DISABLED)
            self.process_btn.config(state=tk.DISABLED)

    def _browse_directory(self, var):
        directory = filedialog.askdirectory()
        if directory:
            var.set(directory)
            self._log_activity(f"Directory set: {directory}")

    def _validate_selected(self):
        if not self.selected_file:
            return

        if not self.download_dir.get():
            messagebox.showerror("Error", "Please set a download directory first.")
            return

        self._log_activity(f"Starting validation for: {self.selected_file}")

        # Download to temp
        local_path = os.path.join(self.download_dir.get(), self.selected_file)
        success, msg = self.ftp_client.download_file(self.selected_file, local_path)

        if not success:
            self._log_activity(f"ERROR: {msg}")
            return

        self._log_activity(f"Downloaded to: {local_path}")

        # Check if already processed
        if self.file_tracker.is_processed(local_path):
            self._log_activity(f"WARNING: File {self.selected_file} has already been processed (duplicate detected).")
            os.remove(local_path)
            return

        # Validate
        is_valid, errors = self.validator.validate_file(local_path)

        if is_valid:
            self._log_activity(f"✓ VALIDATION PASSED: {self.selected_file}")
            self._log_activity("  - Filename format: OK")
            self._log_activity("  - Headers: OK")
            self._log_activity("  - Data integrity: OK")
            self._log_activity("  - No duplicates detected.")
        else:
            self._log_activity(f"✗ VALIDATION FAILED: {self.selected_file}")
            for err in errors:
                self._log_activity(f"  [{err['type']}] {err['details']}")

            # Move to errors directory
            errors_dir = self.errors_dir.get() or "."
            os.makedirs(errors_dir, exist_ok=True)
            error_path = os.path.join(errors_dir, self.selected_file)
            shutil.move(local_path, error_path)
            self._log_activity(f"Moved invalid file to: {error_path}")

    def _process_selected(self):
        if not self.selected_file:
            return

        if not self.download_dir.get():
            messagebox.showerror("Error", "Please set a download directory first.")
            return

        if not self.archive_dir.get():
            messagebox.showerror("Error", "Please set an archive directory first.")
            return

        self._log_activity(f"Starting processing for: {self.selected_file}")

        # Download
        local_path = os.path.join(self.download_dir.get(), self.selected_file)
        success, msg = self.ftp_client.download_file(self.selected_file, local_path)

        if not success:
            self._log_activity(f"ERROR: {msg}")
            return

        # Check duplicates
        if self.file_tracker.is_processed(local_path):
            self._log_activity(f"WARNING: File already processed. Skipping.")
            os.remove(local_path)
            return

        # Validate
        is_valid, errors = self.validator.validate_file(local_path)

        if not is_valid:
            self._log_activity(f"Processing aborted: validation failed.")
            errors_dir = self.errors_dir.get() or "."
            os.makedirs(errors_dir, exist_ok=True)
            error_path = os.path.join(errors_dir, self.selected_file)
            shutil.move(local_path, error_path)
            return

        # Archive
        if not self.archive_manager:
            self.archive_manager = ArchiveManager(self.archive_dir.get())

        archive_path = self.archive_manager.archive_file(local_path, self.selected_file)
        self.file_tracker.mark_processed(local_path)

        self._log_activity(f"✓ File archived to: {archive_path}")
        self._log_activity(f"✓ File marked as processed (hash tracked).")

        # Clean up download
        os.remove(local_path)
        self._log_activity(f"Cleaned up temporary file.")

    def _open_error_log(self):
        log_window = tk.Toplevel(self.root)
        log_window.title("Error Log")
        log_window.geometry("800x500")
        log_window.configure(bg='#e0e0e0')

        text = scrolledtext.ScrolledText(log_window, wrap=tk.WORD, font=('Courier New', 9))
        text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        entries = self.error_log.get_entries()
        if not entries:
            text.insert(tk.END, "No error log entries found.")
        else:
            text.insert(tk.END, f"Total Error Entries: {len(entries)}\n")
            text.insert(tk.END, "=" * 80 + "\n\n")
            for entry in entries:
                text.insert(tk.END, f"UUID: {entry['uuid']}\n")
                text.insert(tk.END, f"Time: {entry['timestamp']}\n")
                text.insert(tk.END, f"File: {entry['filename']}\n")
                text.insert(tk.END, f"Type: {entry['error_type']}\n")
                text.insert(tk.END, f"Details: {entry['error_details']}\n")
                text.insert(tk.END, "-" * 80 + "\n\n")

        text.config(state=tk.DISABLED)

    def _clear_activity(self):
        self.activity_text.config(state=tk.NORMAL)
        self.activity_text.delete(1.0, tk.END)
        self.activity_text.config(state=tk.DISABLED)
        self._log_activity("Activity feed cleared.")

    def _log_activity(self, message):
        self.activity_text.config(state=tk.NORMAL)
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.activity_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.activity_text.see(tk.END)
        self.activity_text.config(state=tk.DISABLED)


# ============================================================================
# TEST DATA GENERATOR (for development/testing)
# ============================================================================
def generate_test_csv_files(output_dir="test_data"):
    """Generate valid and invalid test CSV files for testing."""
    os.makedirs(output_dir, exist_ok=True)

    # Valid file
    valid_filename = "SALE_DATA_20260715083000.csv"
    valid_path = os.path.join(output_dir, valid_filename)
    with open(valid_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["transaction_id", "timestamp", "store_id", "product_id", 
                        "quantity", "unit_price", "total_amount", "payment_method"])
        writer.writerow([686955, "2026-07-15 08:30:00", 2, 3053, 21, 84.55, 1775.55, "credit_card"])
        writer.writerow([933200, "2026-07-15 08:30:00", 15, 5737, 37, 243.40, 9005.80, "debit_card"])
        writer.writerow([728579, "2026-07-15 08:30:00", 18, 3632, 11, 18.08, 198.88, "cash"])

    # Invalid: duplicate transaction_id
    dup_filename = "SALE_DATA_20260715083100.csv"
    dup_path = os.path.join(output_dir, dup_filename)
    with open(dup_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["transaction_id", "timestamp", "store_id", "product_id", 
                        "quantity", "unit_price", "total_amount", "payment_method"])
        writer.writerow([686955, "2026-07-15 08:31:00", 2, 3053, 21, 84.55, 1775.55, "credit_card"])
        writer.writerow([686955, "2026-07-15 08:31:00", 3, 3054, 22, 84.55, 1859.10, "credit_card"])

    # Invalid: bad filename
    bad_name_path = os.path.join(output_dir, "bad_name.csv")
    with open(bad_name_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["transaction_id", "timestamp", "store_id", "product_id", 
                        "quantity", "unit_price", "total_amount", "payment_method"])
        writer.writerow([111111, "2026-07-15 08:32:00", 1, 1001, 10, 50.00, 500.00, "cash"])

    # Invalid: wrong headers
    bad_header_path = os.path.join(output_dir, "SALE_DATA_20260715083300.csv")
    with open(bad_header_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["trans_id", "timestamp", "store_id", "product_id", 
                        "quantity", "unit_price", "total_amount", "payment_method"])
        writer.writerow([222222, "2026-07-15 08:33:00", 1, 1001, 10, 50.00, 500.00, "cash"])

    # Invalid: negative quantity
    neg_qty_path = os.path.join(output_dir, "SALE_DATA_20260715083400.csv")
    with open(neg_qty_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["transaction_id", "timestamp", "store_id", "product_id", 
                        "quantity", "unit_price", "total_amount", "payment_method"])
        writer.writerow([333333, "2026-07-15 08:34:00", 1, 1001, -5, 50.00, -250.00, "cash"])

    # Invalid: incorrect total
    bad_total_path = os.path.join(output_dir, "SALE_DATA_20260715083500.csv")
    with open(bad_total_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["transaction_id", "timestamp", "store_id", "product_id", 
                        "quantity", "unit_price", "total_amount", "payment_method"])
        writer.writerow([444444, "2026-07-15 08:35:00", 1, 1001, 10, 50.00, 999.99, "cash"])

    # Empty file
    empty_path = os.path.join(output_dir, "SALE_DATA_20260715083600.csv")
    with open(empty_path, 'w', encoding='utf-8') as f:
        pass

    # Invalid: missing columns
    missing_col_path = os.path.join(output_dir, "SALE_DATA_20260715083700.csv")
    with open(missing_col_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["transaction_id", "timestamp", "store_id", "product_id", 
                        "quantity", "unit_price", "total_amount", "payment_method"])
        writer.writerow([555555, "2026-07-15 08:37:00", 1, 1001, 10, 50.00])

    print(f"Test files generated in: {os.path.abspath(output_dir)}")
    return output_dir


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================
if __name__ == "__main__":
    import sys

    # Check for test data generation flag
    if len(sys.argv) > 1 and sys.argv[1] == "--generate-test-data":
        generate_test_csv_files()
        sys.exit(0)

    # Launch GUI
    root = tk.Tk()
    app = SaleDataApp(root)
    root.mainloop()