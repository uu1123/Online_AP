import pytest
from ftplib import FTP

@pytest.fixture
def ftp_connection():
    print("Connectng to FTP server")
    
    ftp=FTP("127.0.0.1")
    ftp.login("chew","888")
    
    yield ftp
    print("Closing FTP connection")
    ftp.quit()
    
def test_ftp_connection(ftp_connection):
    files = ftp_connection.nlst()
    assert isinstance(files, list)
    assert len(files) > 0