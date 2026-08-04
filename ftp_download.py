from ftplib import FTP
import os

# ==========================
# FTP Server Configuration
# ==========================
FTP_HOST = "127.0.0.1"      # FTP Server IP Address
FTP_USER = "mmt"            # FTP Username
FTP_PASS = "123"            # FTP Password

REMOTE_DIR = "/"            # Remote folder
LOCAL_DIR = "Files"         # Local download folder


def csv_file_download_from_ftp():
    print("======================================")
    print("Starting FTP Connection Test")
    print("======================================")

    # ------------------------------
    # Connect to FTP Server
    # ------------------------------
    try:
        ftp = FTP(FTP_HOST)
        ftp.login(user=FTP_USER, passwd=FTP_PASS)
        print("[OK] Connected to FTP server.")

    except Exception as e:
        print("[ERROR] FTP connection failed.")
        print(e)
        return

    # ------------------------------
    # Change Remote Directory
    # ------------------------------
    try:
        ftp.cwd(REMOTE_DIR)
        print(f"[OK] Changed to directory: {REMOTE_DIR}")

    except Exception as e:
        print("[ERROR] Cannot change directory.")
        print(e)
        ftp.quit()
        return

    # ------------------------------
    # Create Local Folder
    # ------------------------------
    os.makedirs(LOCAL_DIR, exist_ok=True)

    # ------------------------------
    # Get File List
    # ------------------------------
    try:
        files = ftp.nlst()

    except Exception as e:
        print("[ERROR] Unable to list files.")
        print(e)
        ftp.quit()
        return

    if len(files) == 0:
        print("[INFO] No files found.")
        ftp.quit()
        return

    print(f"\nFound {len(files)} file(s).\n")

    # ------------------------------
    # Process Each File
    # ------------------------------
    for filename in files:

        print("--------------------------------------")
        print(f"Checking: {filename}")

        # Skip non-CSV files
        if not filename.lower().endswith(".csv"):
            print("[SKIP] Not a CSV file.")
            continue

        # Check file size
        try:
            size = ftp.size(filename)

            if size == 0:
                print("[ERROR] File is empty.")
                continue

        except Exception as e:
            print("[ERROR] Cannot determine file size.")
            print(e)
            continue

        # Download file
        local_path = os.path.join(LOCAL_DIR, filename)

        try:
            with open(local_path, "wb") as file:
                ftp.retrbinary("RETR " + filename, file.write)

            print("[OK] Download completed.")
            print(f"Saved to: {local_path}")

        except Exception as e:
            print("[ERROR] Download failed.")
            print(e)

    # ------------------------------
    # Close FTP Connection
    # ------------------------------
    ftp.quit()

    print("\n======================================")
    print("FTP Test Completed")
    print("Connection Closed")
    print("======================================")



csv_file_download_from_ftp()