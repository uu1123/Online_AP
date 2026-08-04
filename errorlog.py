import os
import json
from datetime import datetime


APP_TITLE = "Sales Data Validation System"


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