import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from ftplib import FTP
from datetime import datetime
import os

# UI layout
COLOR_BG_MAIN = "#D5E0E2"
COLOR_PANEL_BG = "#BCD1D4"
COLOR_HEADER_TEAL = "#376E77"
COLOR_BTN_TEAL = "#2E5E66"
COLOR_CREAM = "#F7F3E3"
COLOR_TEXT_DARK = "#222222"

class FTPClientGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("NexusDynamic")
        self.root.geometry("1100x650")
        self.root.configure(bg=COLOR_BG_MAIN)

        self.ftp = None
        self.all_files = []

        # Configure global styles
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure('.', background=COLOR_BG_MAIN, foreground=COLOR_TEXT_DARK)

        self.setup_ui()
        self.log_event("Activity Feed initialized.")

    def setup_ui(self):
        # 1. TOP TITLE BAR
        title_frame = tk.Frame(self.root, bg=COLOR_BG_MAIN, padx=15, pady=10)
        title_frame.pack(fill="x")

        title_label = tk.Label(
            title_frame, text="Nexus Dynamic",
            font=("Arial", 16, "bold"), fg=COLOR_HEADER_TEAL, bg=COLOR_BG_MAIN
        )
        title_label.pack(side="left")

        self.status_label = tk.Label(
            title_frame, text="● Disconnected",
            font=("Arial", 11), fg="#B22222", bg=COLOR_BG_MAIN
        )
        self.status_label.pack(side="right", padx=10)

        # 2. content?
        middle_frame = tk.Frame(self.root, bg=COLOR_BG_MAIN, padx=10)
        middle_frame.pack(fill="both", expand=True)

        # FTP connection left panel
        left_panel = tk.LabelFrame(
            middle_frame, text="Connection & Browser", font=("Arial", 11, "bold"),
            bg=COLOR_PANEL_BG, fg="white", labelanchor="nw", bd=0, relief="flat"
        )
        left_panel.pack(side="left", fill="both", expand=True, padx=5, pady=5)

        # 1. Host Connection Sub-section
        conn_frame = tk.Frame(left_panel, bg=COLOR_PANEL_BG, padx=10, pady=10)
        conn_frame.place(relx=0, rely=0, relwidth=0.45, relheight=1)

        tk.Label(conn_frame, text="1. Host Connection", font=("Arial", 11, "bold"), bg=COLOR_PANEL_BG, fg=COLOR_TEXT_DARK).pack(anchor="w", pady=(0, 10))

        tk.Label(conn_frame, text="Host", bg=COLOR_PANEL_BG, fg=COLOR_TEXT_DARK).pack(anchor="w")
        self.host_entry = tk.Entry(conn_frame, bg=COLOR_CREAM, bd=1, relief="solid")
        self.host_entry.pack(fill="x", pady=(0, 10), ipady=3)
        self.host_entry.insert(0, "127.0.0.1")

        tk.Label(conn_frame, text="Username", bg=COLOR_PANEL_BG, fg=COLOR_TEXT_DARK).pack(anchor="w")
        self.user_entry = tk.Entry(conn_frame, bg=COLOR_CREAM, bd=1, relief="solid")
        self.user_entry.pack(fill="x", pady=(0, 10), ipady=3)

        tk.Label(conn_frame, text="Password", bg=COLOR_PANEL_BG, fg=COLOR_TEXT_DARK).pack(anchor="w")
        self.pass_entry = tk.Entry(conn_frame, show="*", bg=COLOR_CREAM, bd=1, relief="solid")
        self.pass_entry.pack(fill="x", pady=(0, 20), ipady=3)

        # Bind Enter keys to connect
        self.host_entry.bind("<Return>", lambda e: self.connect())
        self.user_entry.bind("<Return>", lambda e: self.connect())
        self.pass_entry.bind("<Return>", lambda e: self.connect())

        btn_conn_frame = tk.Frame(conn_frame, bg=COLOR_PANEL_BG)
        btn_conn_frame.pack(fill="x")

        self.btn_connect = tk.Button(btn_conn_frame, text="Connect", bg=COLOR_BTN_TEAL, fg="white", activebackground=COLOR_HEADER_TEAL, command=self.connect, width=10, relief="flat")
        self.btn_connect.pack(side="left", padx=(0, 5))

        self.btn_disconnect = tk.Button(btn_conn_frame, text="Disconnect", bg="#7A9A9E", fg="white", command=self.disconnect, width=10, relief="flat")
        self.btn_disconnect.pack(side="left")

        # 2. Server Browser Sub-section
        browser_frame = tk.Frame(left_panel, bg=COLOR_PANEL_BG, padx=10, pady=10)
        browser_frame.place(relx=0.45, rely=0, relwidth=0.55, relheight=1)

        tk.Label(browser_frame, text="2. Server Browser", font=("Arial", 11, "bold"), bg=COLOR_PANEL_BG, fg=COLOR_TEXT_DARK).pack(anchor="w", pady=(0, 5))

        search_bar_frame = tk.Frame(browser_frame, bg=COLOR_PANEL_BG)
        search_bar_frame.pack(fill="x", pady=(0, 5))

        tk.Label(search_bar_frame, text="Filter:", bg=COLOR_PANEL_BG, fg=COLOR_TEXT_DARK).pack(side="left", padx=(0, 5))
        self.search_entry = tk.Entry(search_bar_frame, bg=COLOR_CREAM, bd=1, relief="solid")
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(0, 5), ipady=2)
        self.search_entry.bind("<Return>", lambda e: self.filter_files())

        tk.Button(search_bar_frame, text="Apply", bg=COLOR_BTN_TEAL, fg="white", command=self.filter_files, relief="flat", padx=5).pack(side="left", padx=2)
        tk.Button(search_bar_frame, text="Res", bg=COLOR_BTN_TEAL, fg="white", command=self.clear_search, relief="flat", padx=5).pack(side="left")

        #  file list
        self.file_list = tk.Listbox(browser_frame, bg=COLOR_CREAM, fg=COLOR_TEXT_DARK, bd=1, relief="solid", highlightthickness=0)
        self.file_list.pack(fill="both", expand=True)

        # workspace + action(validate, process, select)
        right_panel = tk.LabelFrame(
            middle_frame, text="Workspace & Actions", font=("Arial", 11, "bold"),
            bg=COLOR_PANEL_BG, fg="white", labelanchor="nw", bd=0, relief="flat"
        )
        right_panel.pack(side="right", fill="both", expand=True, padx=5, pady=5)

        work_inner = tk.Frame(right_panel, bg=COLOR_PANEL_BG, padx=15, pady=10)
        work_inner.pack(fill="both", expand=True)

        # Helper method to generate path inputs quickly
        def create_path_row(parent, label_text):
            tk.Label(parent, text=label_text, bg=COLOR_PANEL_BG, fg=COLOR_TEXT_DARK).pack(anchor="w", pady=(5, 0))
            row = tk.Frame(parent, bg=COLOR_PANEL_BG)
            row.pack(fill="x", pady=(2, 8))

            entry = tk.Entry(row, bg=COLOR_CREAM, bd=1, relief="solid")
            entry.pack(side="left", fill="x", expand=True, ipady=3, padx=(0, 5))

            btn = tk.Button(
                row, text="📁 Browse...", bg=COLOR_BTN_TEAL, fg="white",
                command=lambda: self.browse_directory(entry), relief="flat", padx=8
            )
            btn.pack(side="right")
            return entry

        self.dir_download = create_path_row(work_inner, "Download directory")
        self.dir_archive = create_path_row(work_inner, "Archive directory")
        self.dir_errors = create_path_row(work_inner, "Errors directory")

        # Action grids inside the Workspace
        actions_grid = tk.Frame(work_inner, bg=COLOR_PANEL_BG, pady=15)
        actions_grid.pack(fill="x", expand=True, side="bottom")

        # row1 actions
        tk.Button(actions_grid, text=" Validate Selected File", bg=COLOR_BTN_TEAL, fg="white", font=("Arial", 10), command=self.validate_file, relief="flat", height=2).grid(row=0, column=0, sticky="ew", padx=2, pady=2)
        tk.Button(actions_grid, text=" Process Selected File", bg=COLOR_BTN_TEAL, fg="white", font=("Arial", 10), command=self.process_file, relief="flat", height=2).grid(row=0, column=1, sticky="ew", padx=2, pady=2)

        #row2 actions
        tk.Button(actions_grid, text="Open Error Log", bg=COLOR_BTN_TEAL, fg="white", font=("Arial", 10), command=self.open_error_log, relief="flat", height=2).grid(row=1, column=0, sticky="ew", padx=2, pady=2)
        tk.Button(actions_grid, text="Clear Activity Feed", bg=COLOR_BTN_TEAL, fg="white", font=("Arial", 10), command=self.clear_log_history, relief="flat", height=2).grid(row=1, column=1, sticky="ew", padx=2, pady=2)

        actions_grid.grid_columnconfigure(0, weight=1)
        actions_grid.grid_columnconfigure(1, weight=1)

        # Activity Log
        bottom_panel = tk.LabelFrame(
            self.root, text="Activity Feed", font=("Arial", 11, "bold"),
            bg=COLOR_PANEL_BG, fg="white", labelanchor="nw", bd=0, relief="flat"
        )
        bottom_panel.pack(fill="x", side="bottom", padx=15, pady=(5, 15))

        log_frame = tk.Frame(bottom_panel, bg=COLOR_CREAM, padx=5, pady=5)
        log_frame.pack(fill="both", expand=True, padx=2, pady=2)

        self.log_list = tk.Listbox(
            log_frame, bg=COLOR_CREAM, fg=COLOR_TEXT_DARK,
            height=6, bd=0, highlightthickness=0, font=("Courier New", 10)
        )
        self.log_list.pack(side="left", fill="both", expand=True)

        log_scroll = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_list.yview)
        log_scroll.pack(side="right", fill="y")
        self.log_list.config(yscrollcommand=log_scroll.set)

    # for browser directory
    def browse_directory(self, target_entry):
        selected_dir = filedialog.askdirectory()
        if selected_dir:
            target_entry.delete(0, tk.END)
            target_entry.insert(0, os.path.normpath(selected_dir))
            self.log_event(f"Selected directory path: {selected_dir}")

    # main FTP
    def log_event(self, message):
        self.log_list.insert(tk.END, message)
        self.log_list.see(tk.END)

    def clear_log_history(self):
        self.log_list.delete(0, tk.END)
        self.log_event("Activity Feed cleared.")

    def connect(self):
        host = self.host_entry.get().strip()
        username = self.user_entry.get().strip()
        password = self.pass_entry.get()

        if not host:
            self.log_event("Connection failed: Host field is empty.")
            messagebox.showwarning("Warning", "Please enter a host address.")
            return

        self.log_event(f"Attempting connection to {host}...")

        try:
            self.ftp = FTP(host, timeout=10)
            self.ftp.login(username, password)

            self.status_label.config(text="● Connected", fg="#2E8B57")
            self.log_event("Connected and authenticated successfully.")
            messagebox.showinfo("Success", "FTP Connected Successfully!")

            self.file_list.delete(0, tk.END)
            self.search_entry.delete(0, tk.END)
            self.all_files = []

            files = self.ftp.nlst()
            if files:
                self.all_files = files
                for file in files:
                    self.file_list.insert(tk.END, file)
                self.log_event(f"Loaded {len(files)} files/directories.")
            else:
                self.file_list.insert(tk.END, "No files found")
                self.log_event("Directory listing returned empty.")

        except Exception as e:
            self.file_list.delete(0, tk.END)
            self.all_files = []
            self.status_label.config(text="● Disconnected", fg="#B22222")
            self.log_event(f"Error during connection: {str(e)}")
            messagebox.showerror("FTP Error", str(e))

    def filter_files(self):
        search_term = self.search_entry.get().strip().lower()
        if not self.ftp:
            self.log_event("Search ignored: Not connected to an FTP server.")
            return

        self.log_event(f"Filtering files with query: '{search_term}'")
        self.file_list.delete(0, tk.END)

        filtered_files = [f for f in self.all_files if search_term in f.lower()]
        if filtered_files:
            for file in filtered_files:
                self.file_list.insert(tk.END, file)
        else:
            self.file_list.insert(tk.END, "No matching files found")
            self.log_event("No search results found.")

    def clear_search(self):
        self.search_entry.delete(0, tk.END)
        self.file_list.delete(0, tk.END)
        if self.all_files:
            for file in self.all_files:
                self.file_list.insert(tk.END, file)
            self.log_event("Search filter cleared.")
        elif self.ftp:
            self.file_list.insert(tk.END, "No files found")

    def disconnect(self):
        if self.ftp:
            try:
                self.ftp.quit()
                messagebox.showinfo("Disconnected", "FTP connection closed.")
            except Exception:
                pass
            finally:
                self.ftp = None

        self.status_label.config(text="● Disconnected", fg="#B22222")
        self.all_files = []
        self.search_entry.delete(0, tk.END)
        self.file_list.delete(0, tk.END)
        self.log_event("No connection between server and database.")

    # more features
    def validate_file(self):
        selected = self.file_list.curselection()
        if not selected:
            messagebox.showwarning("Validation", "Please select a file from the server browser first.")
            return
        filename = self.file_list.get(selected[0])
        self.log_event(f"Log log validatet selected... File: {filename}")

    def process_file(self):
        selected = self.file_list.curselection()
        if not selected:
            messagebox.showwarning("Process File", "Please select a file to process.")
            return
        filename = self.file_list.get(selected[0])
        self.log_event(f"Processing selected file: {filename}...")

    def open_error_log(self):
        self.log_event("Opening local error log file...")


if __name__ == "__main__":
    root = tk.Tk()
    app = FTPClientGUI(root)
    root.mainloop()
