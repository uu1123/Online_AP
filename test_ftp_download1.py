import os
import pytest
import ftp_download

# ==========================
# Fixtures
# ==========================

@pytest.fixture
def download_folder():

    folder = "Files"

    # Create folder if not exists
    os.makedirs(folder, exist_ok=True)

    return folder


@pytest.fixture
def ftp_server():

    # Real FTP server information
    return {
        "host": ftp_download.FTP_HOST,
        "user": ftp_download.FTP_USER,
        "password": ftp_download.FTP_PASS
    }


# ==========================
# Tests
# ==========================

def test_ftp_connection(ftp_server):
    """
    Test FTP connection
    """
    ftp_download.csv_file_download_from_ftp()

    assert True


def test_download_csv_file(download_folder, ftp_server):
    """
    Test CSV files are downloaded
    """
    # Run FTP download
    ftp_download.csv_file_download_from_ftp()

    files = os.listdir(download_folder)

    csv_files = []

    for file in files:

        if file.lower().endswith(".csv"):
            csv_files.append(file)

    assert len(csv_files) > 0

def test_downloaded_files_are_csv(download_folder, ftp_server):
    """
    Check all downloaded files have .csv extension
    """
    ftp_download.csv_file_download_from_ftp()
    files = os.listdir(download_folder)
    for file in files:

        if os.path.isfile(
            os.path.join(download_folder, file)
        ):
            assert file.lower().endswith(".csv")

def test_downloaded_files_not_empty(download_folder, ftp_server):
    """
    Check downloaded CSV files are not empty
    """
    ftp_download.csv_file_download_from_ftp()
    files = os.listdir(download_folder)

    for file in files:

        path = os.path.join(
            download_folder,
            file
        )
        if os.path.isfile(path):

            size = os.path.getsize(path)

            assert size > 0