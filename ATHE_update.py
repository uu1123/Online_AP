import csv
import datetime
import json
import os
import re
import urllib.request
import uuid
from ftplib import FTP
import tkinter as tk
from tkinter import filedialog, messagebox, ttk


class SalesValidationSystem(tk.Tk):

    def __init__(self):
        super().__init__()
        self.title("Sales Data Validation System")
        self.geometry("1100x700")
        self.configure(bg="#C0DDDA")

        self.is_connected = False
        self.ftp = None
        self.all_files = []

        style = ttk.Style()
        style.theme_use("clam")

        frame1 = tk.Frame(self, bg="#C0DDDA")
        frame1.pack(fill="x", padx=15, pady=10)

        frame1_label = tk.Label(
            frame1,
            text="SALE DATA VALIDATION SYSTEM",
            font=("Arial", 14, "bold"),
            bg="#C0DDDA",
        )
        frame1_label.pack(side="left", pady=5)

        self.status_label = tk.Label(
            frame1,
            text="Disconnected",
            font=("Arial", 10, "bold"),
            bg="#C0DDDA",
            foreground="#555555",
        )
        self.status_label.pack(side="right", pady=5, padx=10)

        # Main Layout Frame
        top_panels_frame = tk.Frame(self, bg="#C0DDDA")
        top_panels_frame.pack(fill="x", padx=10, pady=5)

        # 1. Connection Panel
        connection_frame = ttk.LabelFrame(
            top_panels_frame, text="Connection", width=200, height=280
        )
        connection_frame.pack(side="left", padx=5, pady=5)
        connection_frame.pack_propagate(False)

        host_label = tk.Label(connection_frame, text="FTP Host", anchor="w")
        host_label.pack(fill="x", padx=10, pady=(10, 2))

        self.host_entry = ttk.Entry(connection_frame, width=25)
        self.host_entry.insert(0, "127.0.0.1")
        self.host_entry.pack(padx=10, pady=(0, 15))

        user_label = tk.Label(connection_frame, text="Username", anchor="w")
        user_label.pack(fill="x", padx=10, pady=(2, 2))

        user_var = tk.StringVar(value="chew")
        self.user_entry = ttk.Entry(
            connection_frame, width=25, textvariable=user_var
        )
        self.user_entry.pack(padx=10, pady=(0, 15))

        pass_label = tk.Label(connection_frame, text="Password", anchor="w")
        pass_label.pack(fill="x", padx=10, pady=(2, 2))

        pass_var = tk.StringVar(value="882007")
        self.pass_entry = ttk.Entry(
            connection_frame, show="*", width=25, textvariable=pass_var
        )
        self.pass_entry.pack(padx=10, pady=(0, 15))

        conn_btn_frame = tk.Frame(connection_frame)
        conn_btn_frame.pack(fill="x", padx=10, pady=(0, 15))

        self.connect_btn = ttk.Button(
            conn_btn_frame,
            text="Connect",
            width=10,
            command=self.connect_ftp,
        )
        self.connect_btn.pack(side="left", padx=(0, 5))

        self.disconnect_btn = ttk.Button(
            conn_btn_frame,
            text="Disconnect",
            width=12,
            command=self.disconnect_ftp,
        )
        self.disconnect_btn.pack(side="left")

        # 2. Server Browser Panel
        browser_frame = ttk.LabelFrame(
            top_panels_frame, text="Server Browser", width=1100, height=280
        )
        browser_frame.pack(side="left", padx=5, pady=5)
        browser_frame.pack_propagate(False)

        filter_frame = tk.Frame(browser_frame)
        filter_frame.pack(fill="x", padx=10, pady=10)

        filter_label = tk.Label(filter_frame, text="Filter:")
        filter_label.pack(side="left", padx=(0, 5))

        self.filter_entry = ttk.Entry(filter_frame)
        self.filter_entry.pack(
            side="left", fill="x", expand=True, padx=(0, 5)
        )

        apply_btn = ttk.Button(
            filter_frame, text="Apply", width=6, command=self.filter_files
        )
        apply_btn.pack(side="left", padx=(0, 2))

        res_btn = ttk.Button(
            filter_frame, text="Res", width=5, command=self.clear_search
        )
        res_btn.pack(side="left")

        listbox_frame = tk.Frame(browser_frame)
        listbox_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        scrollbar = tk.Scrollbar(listbox_frame)
        scrollbar.pack(side="right", fill="y")

        self.server_listbox = tk.Listbox(
            listbox_frame,
            bd=1,
            height=10,
            background="white",
            yscrollcommand=scrollbar.set,
        )
        self.server_listbox.pack(fill="both", expand=True)
        scrollbar.config(command=self.server_listbox.yview)

        # 3. Workspace & Actions Panel
        workspace_frame = ttk.LabelFrame(
            self, text="Workspace & Actions", width=600, height=300
        )
        workspace_frame.pack(side="left", padx=15, pady=5)
        workspace_frame.pack_propagate(False)

        download_label = tk.Label(
            workspace_frame, text="Download directory", anchor="w"
        )
        download_label.pack(fill="x", padx=10, pady=(5, 2))

        dir1_frame = tk.Frame(workspace_frame)
        dir1_frame.pack(fill="x", padx=10, pady=(0, 5))
        self.dir1_entry = ttk.Entry(dir1_frame)
        self.dir1_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        dir1_btn = ttk.Button(
            dir1_frame,
            text="Browse...",
            width=10,
            command=lambda: self.browse_directory(self.dir1_entry),
        )
        dir1_btn.pack(side="right")

        archive_label = tk.Label(
            workspace_frame,
            text="Archive (Correct Files) directory",
            anchor="w",
        )
        archive_label.pack(fill="x", padx=10, pady=(5, 2))

        dir2_frame = tk.Frame(workspace_frame)
        dir2_frame.pack(fill="x", padx=10, pady=(0, 5))
        self.dir2_entry = ttk.Entry(dir2_frame)
        self.dir2_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        dir2_btn = ttk.Button(
            dir2_frame,
            text="Browse...",
            width=10,
            command=lambda: self.browse_directory(self.dir2_entry),
        )
        dir2_btn.pack(side="right")

        errors_label = tk.Label(
            workspace_frame, text="Errors directory", anchor="w"
        )
        errors_label.pack(fill="x", padx=10, pady=(5, 2))

        dir3_frame = tk.Frame(workspace_frame)
        dir3_frame.pack(fill="x", padx=10, pady=(0, 10))
        self.dir3_entry = ttk.Entry(dir3_frame)
        self.dir3_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        dir3_btn = ttk.Button(
            dir3_frame,
            text="Browse...",
            width=10,
            command=lambda: self.browse_directory(self.dir3_entry),
        )
        dir3_btn.pack(side="right")

        validate_btn = ttk.Button(
            workspace_frame,
            text="Validate Selected File",
            command=self.validate_selected_file,
        )
        validate_btn.pack(side="left", padx=10, pady=2)

        process_btn = ttk.Button(
            workspace_frame,
            text="Process Selected File",
            command=self.process_selected_file,
        )
        process_btn.pack(side="left", padx=10, pady=2)

        open_log_btn = ttk.Button(
            workspace_frame, text="Open Error Log", command=self.open_error_log
        )
        open_log_btn.pack(side="left", padx=10, pady=2)

        clear_feed_btn = ttk.Button(
            workspace_frame,
            text="Clear Activity Feed",
            command=self.clear_activity_feed,
        )
        clear_feed_btn.pack(side="left", padx=10, pady=2)

        # 4. Activity Feed Panel
        activity_frame = ttk.LabelFrame(
            self, text="Activity Feed", width=750, height=300
        )
        activity_frame.pack(side="left", padx=15, pady=(5, 15))
        activity_frame.pack_propagate(False)

        self.activity_text_box = tk.Text(
            activity_frame, bg="white", bd=1, height=8
        )
        self.activity_text_box.pack(fill="both", expand=True, padx=10, pady=10)

        self.log_activity("Sale Data Console initialized.")
        self.log_activity(
            "Ready for connection. Please configure FTP settings."
        )

    def log_activity(self, message):
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        self.activity_text_box.insert(tk.END, f"[{timestamp}] {message}\n")
        self.activity_text_box.see(tk.END)

    def fetch_uuid_v1(self):
        """Fetches a UUID v1 from the external API with a local uuid.uuid1() fallback."""
        url = "https://www.uuidtools.com/api/generate/v1"
        try:
            req = urllib.request.Request(
                url, headers={"User-Agent": "Mozilla/5.0"}
            )
            with urllib.request.urlopen(req, timeout=3) as response:
                data = json.loads(response.read().decode("utf-8"))
                if isinstance(data, list) and len(data) > 0:
                    return str(data[0])
        except Exception as e:
            self.log_activity(
                f"API UUID v1 fetch failed ({e}). Using local uuid.uuid1()."
            )
        return str(uuid.uuid1())

    def browse_directory(self, entry_widget):
        selected_dir = filedialog.askdirectory()
        if selected_dir:
            entry_widget.delete(0, tk.END)
            entry_widget.insert(0, os.path.normpath(selected_dir))
            self.log_activity(
                f"Directory configuration linked: {selected_dir}"
            )

    def clear_activity_feed(self):
        self.activity_text_box.delete("1.0", tk.END)

    def connect_ftp(self):
        if self.is_connected:
            return

        host = self.host_entry.get().strip()
        username = self.user_entry.get().strip()
        password = self.pass_entry.get()

        if not host:
            self.log_activity("Connection failed: Host field is empty.")
            messagebox.showwarning("Warning", "Please enter a host address.")
            return

        self.log_activity(f"Connecting to {host}...")

        try:
            self.ftp = FTP(host, timeout=10)
            self.ftp.login(username, password)

            self.log_activity("Connected successfully.")
            self.status_label.config(text="Connected", foreground="#2E7D32")
            self.is_connected = True

            self.server_listbox.delete(0, tk.END)
            self.filter_entry.delete(0, tk.END)
            self.all_files = []

            try:
                files = self.ftp.nlst()
                if files:
                    self.all_files = files
                    for file in files:
                        self.server_listbox.insert(tk.END, file)
                    self.log_activity(
                        f"Found {len(files)} files on server."
                    )
                else:
                    self.server_listbox.insert(tk.END, "No files found")
                    self.log_activity("Directory listing returned empty.")
            except Exception as list_err:
                self.server_listbox.insert(
                    tk.END, "Could not fetch directory listing"
                )
                self.log_activity(f"Listing error: {str(list_err)}")

        except Exception as e:
            self.server_listbox.delete(0, tk.END)
            self.all_files = []
            self.log_activity(f"ERROR: Connection failed: {str(e)}")
            messagebox.showerror("FTP Error", str(e))

    def disconnect_ftp(self):
        if not self.is_connected:
            return

        if self.ftp:
            try:
                self.ftp.quit()
            except Exception:
                pass
            finally:
                self.ftp = None

        self.all_files = []
        self.filter_entry.delete(0, tk.END)
        self.server_listbox.delete(0, tk.END)
        self.log_activity("Disconnected from server.")
        self.status_label.config(text="Disconnected", foreground="#555555")
        self.is_connected = False

    def validate_file(self, filepath, filename):
        """Discrete validation checks pipeline."""
        errors = []

        filename_pattern = r"^SALES_DATA_\d{14}\.csv$"
        if not re.match(filename_pattern, filename):
            errors.append("Incorrect filename format.")

        if os.path.getsize(filepath) == 0:
            errors.append("CSV file is empty (0-byte file).")
            return errors

        required_headers = [
            "transaction_id",
            "timestamp",
            "store_id",
            "product_id",
            "quantity",
            "unit_price",
            "total_amount",
            "payment_method",
        ]

        transaction_ids = set()
        timestamps = []

        try:
            with open(filepath, "r", newline="", encoding="utf-8") as file:
                reader = csv.DictReader(file)

                if reader.fieldnames is None:
                    errors.append("Missing headers.")
                    return errors

                reader.fieldnames = [
                    h.strip().lower() for h in reader.fieldnames
                ]
                headers = reader.fieldnames

                for field in required_headers:
                    if field not in headers:
                        errors.append(f"Missing header: {field}")

                if any(field not in headers for field in required_headers):
                    return errors

                for row_number, row in enumerate(reader, start=2):
                    for field in required_headers:
                        if row[field] is None or row[field].strip() == "":
                            errors.append(f"Row {row_number}: Missing {field}")

                    transaction_id = row["transaction_id"]
                    if transaction_id in transaction_ids:
                        errors.append(
                            f"Row {row_number}: Duplicate transaction_id {transaction_id}"
                        )
                    else:
                        transaction_ids.add(transaction_id)

                    try:
                        datetime.datetime.strptime(
                            row["timestamp"], "%Y-%m-%d %H:%M:%S"
                        )
                        timestamps.append(row["timestamp"])
                    except ValueError:
                        errors.append(
                            f"Row {row_number}: Invalid timestamp format."
                        )

                    try:
                        quantity = int(row["quantity"])
                        unit_price = float(row["unit_price"])
                        total_amount = float(row["total_amount"])

                        if quantity <= 0:
                            errors.append(
                                f"Row {row_number}: Quantity must be positive."
                            )
                        if unit_price <= 0:
                            errors.append(
                                f"Row {row_number}: Unit price must be positive."
                            )
                        if total_amount <= 0:
                            errors.append(
                                f"Row {row_number}: Total amount must be positive."
                            )

                        if abs(quantity * unit_price - total_amount) > 0.01:
                            errors.append(
                                f"Row {row_number}: Total amount calculation incorrect."
                            )
                    except ValueError:
                        errors.append(
                            f"Row {row_number}: Invalid numeric value."
                        )

                if timestamps:
                    first_date = timestamps[0][:10]
                    for index, time_str in enumerate(timestamps, start=2):
                        if time_str[:10] != first_date:
                            errors.append(
                                f"Row {index}: Timestamp inconsistent."
                            )

        except Exception as e:
            errors.append(f"CSV reading error: {str(e)}")

        return errors

    def validate_selected_file(self):
        selected_index = self.server_listbox.curselection()

        if not selected_index:
            messagebox.showwarning("Warning", "Please select a file first.")
            return

        filename = self.server_listbox.get(selected_index)
        filepath = os.path.join(self.dir1_entry.get().strip(), filename)

        if not os.path.exists(filepath):
            messagebox.showwarning("Warning", "File is not downloaded yet.")
            return

        errors = self.validate_file(filepath, filename)

        if errors:
            self.log_activity(f"{filename} failed validation.")
            for error in errors:
                self.log_activity(error)
            messagebox.showerror(
                "Validation Failed", f"{filename} contains errors."
            )
        else:
            self.log_activity(f"{filename} passed validation.")
            messagebox.showinfo("Validation Passed", f"{filename} is valid.")

    def process_selected_file(self):
        download_dir = self.dir1_entry.get().strip()
        archive_dir = self.dir2_entry.get().strip()
        errors_dir = self.dir3_entry.get().strip()

        if not download_dir or not archive_dir or not errors_dir:
            messagebox.showwarning(
                "Warning",
                "Please select your Download, Archive, and Errors directories first.",
            )
            return

        selected_index = self.server_listbox.curselection()
        if not selected_index:
            messagebox.showwarning(
                "Warning", "Please select a file from the server browser first."
            )
            return

        filename = self.server_listbox.get(selected_index)

        os.makedirs(download_dir, exist_ok=True)
        os.makedirs(archive_dir, exist_ok=True)
        os.makedirs(errors_dir, exist_ok=True)

        local_filepath = os.path.join(download_dir, filename)

        if not os.path.exists(local_filepath):
            self.log_activity(
                f"Processing Error: '{filename}' not found in local download directory."
            )
            messagebox.showwarning(
                "Warning",
                f"File '{filename}' does not exist in the specified download directory.",
            )
            return

        self.log_activity(f"Processing file routing for: {filename}")
        errors_found = self.validate_file(local_filepath, filename)

        if not errors_found:
            destination_path = os.path.join(archive_dir, filename)
            os.replace(local_filepath, destination_path)
            self.log_activity(
                f"SUCCESS: Clean file routed to Archive -> {destination_path}"
            )
            messagebox.showinfo(
                "Success",
                "Valid file successfully processed into the Archive folder!",
            )
        else:
            destination_path = os.path.join(errors_dir, filename)
            os.replace(local_filepath, destination_path)

            log_path = os.path.join(errors_dir, "validation_errors.log")
            self._write_and_log_errors(filename, errors_found, log_path)

            self.log_activity(
                f"REJECTED: Malformed file routed to Errors -> {destination_path}"
            )

    def _write_and_log_errors(self, filename, errors, log_path):
        """Generates a UUID v1 for logging while keeping the messagebox clear of UUID text."""
        entry_uuid_v1 = self.fetch_uuid_v1()
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        self.log_activity(f"File '{filename}' FAILED verification rules check.")

        with open(log_path, "a", encoding="utf-8") as log_file:
            log_file.write(f"=== ERROR LOG ENTRY [UUID v1: {entry_uuid_v1}] ===\n")
            log_file.write(f"Timestamp: {timestamp}\n")
            log_file.write(f"Target File: {filename}\n")
            log_file.write("Errors Detected:\n")
            for err in errors:
                self.log_activity(f"  > {err}")
                log_file.write(f"  - {err}\n")
            log_file.write("=" * 50 + "\n\n")

        messagebox.showerror(
            "Validation Failed",
            f"File '{filename}' contains data structural errors. Review full logs for comprehensive audit outputs details.",
        )

    def open_error_log(self):
        errors_dir = self.dir3_entry.get().strip()
        if not errors_dir:
            messagebox.showwarning(
                "Warning", "Please configure your Errors directory pathway first."
            )
            return

        log_filepath = os.path.join(errors_dir, "validation_errors.log")
        if os.path.exists(log_filepath):
            if hasattr(os, "startfile"):
                os.startfile(log_filepath)
            else:
                os.system(f'xdg-open "{log_filepath}"')
        else:
            messagebox.showinfo(
                "Log Empty", "No current system execution log history records found."
            )

    def filter_files(self):
        search_term = self.filter_entry.get().strip().lower()

        if not self.ftp:
            self.log_activity("Search ignored: Not connected to an FTP server.")
            return

        self.server_listbox.delete(0, tk.END)
        filtered_files = [
            f for f in self.all_files if search_term in f.lower()
        ]

        if filtered_files:
            for file in filtered_files:
                self.server_listbox.insert(tk.END, file)
        else:
            self.server_listbox.insert(tk.END, "No matching files found")

    def clear_search(self):
        self.filter_entry.delete(0, tk.END)
        self.server_listbox.delete(0, tk.END)
        if self.all_files:
            for file in self.all_files:
                self.server_listbox.insert(tk.END, file)


if __name__ == "__main__":
    app = SalesValidationSystem()
    app.mainloop()