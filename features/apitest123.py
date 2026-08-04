import requests

url = "https://www.uutools.com/api/generate/v1"

response = requests.get(url)

print("Status Code :", response.status_code)
print("Status      :", response.reason)

if response.ok:
    print("UUID:", response.json()[0])