from ftplib import FTP

class FTPClient:
    def __init__(self, host, user, password):
        self.host = host
        self.user = user
        self.password = password
        self.ftp = None

    def connect(self):
        self.ftp = FTP(self.host)
        self.ftp.login(user=self.user, passwd=self.password)
        return self.ftp

    def disconnect(self):
        if self.ftp:
            self.ftp.quit()