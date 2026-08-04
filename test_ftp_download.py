import os
import pytest
import ftp_download


# -----------------------------
# Fixture
# -----------------------------
@pytest.fixture
def ftp_server():

    ftp_download.FTP_HOST = "127.0.0.1"
    ftp_download.FTP_USER = "mmt"
    ftp_download.FTP_PASS = "123"
    ftp_download.REMOTE_DIR = "/"

    yield

    # cleanup if required


# -----------------------------
# Fixture
# -----------------------------
@pytest.fixture
def download_folder():

    folder = "Files"

    if not os.path.exists(folder):
        os.mkdir(folder)

    yield folder

    # remove downloaded files after test
    for file in os.listdir(folder):
        path = os.path.join(folder, file)

        if os.path.isfile(path):
            os.remove(path)

# connect ftp server
def test_ftp_connection(ftp_server):

    from ftplib import FTP

    ftp = FTP(ftp_download.FTP_HOST)
    ftp.login(
        ftp_download.FTP_USER,
        ftp_download.FTP_PASS
    )

    assert ftp.sock is not None

    ftp.quit()

#download CSV file

def test_download_csv_file(ftp_server, download_folder):

    ftp_download.test_csv_file_download_from_ftp()

    files = os.listdir(download_folder)

    assert len(files) > 0

#download files are CSV

def test_downloaded_files_are_csv(download_folder, ftp_server):

    ftp_download.test_csv_file_download_from_ftp()

    files = os.listdir(download_folder)

    for file in files:
        assert file.endswith(".csv")
#download files are not empty

def test_downloaded_files_not_empty(download_folder, ftp_server):

    ftp_download.test_csv_file_download_from_ftp()

    files = os.listdir(download_folder)

    for file in files:
        path = os.path.join(download_folder, file)

        assert os.path.getsize(path) > 0