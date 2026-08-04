import pytest
from ftp_client import FTPClient

# FTP server credentials
FTP_HOST = "127.0.0.1"
FTP_USER = "mmt"
FTP_PASS = "123"

@pytest.fixture
def ftp_connection():
    """
    Fixture to create and close an FTP connection.
    """
    client = FTPClient(FTP_HOST, FTP_USER, FTP_PASS)
    ftp = client.connect()

    yield ftp

    client.disconnect()


def test_ftp_login(ftp_connection):
    """
    Verify that login to the FTP server succeeds.
    """
    assert ftp_connection is not None


def test_server_response(ftp_connection):
    """
    Verify that the FTP server returns a welcome message.
    """
    welcome = ftp_connection.getwelcome()

    assert isinstance(welcome, str)
    assert len(welcome) > 0


def test_current_directory(ftp_connection):
    """
    Verify that the current working directory exists.
    """
    current_directory = ftp_connection.pwd()

    assert isinstance(current_directory, str)
    assert current_directory != ""