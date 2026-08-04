from ftplib import FTP

# FTP server credentials
ftp_host = '127.0.0.1'      # FTP server address
ftp_user = 'mmt'            # FTP username
ftp_pass = '123'            # FTP password

try:
    # Connect to FTP server
    ftp = FTP(ftp_host)
    ftp.login(user=ftp_user, passwd=ftp_pass)

    print("!!Connected and logged in to the FTP server successfully.")

    # Optional: Print welcome message or current directory
    print("Server response:", ftp.getwelcome())
    print("Current directory:", ftp.pwd())

    # Disconnect
    ftp.quit()
    # print("Disconnected from the FTP server.")

except Exception as e:
    print(f"FTP connection failed: {e}")