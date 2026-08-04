import requests
from datetime import datetime

def generate_uuid():
    url = "https://www.uuidtools.com/api/generate/v1"

    try:
        response = requests.get(url)

        if response.status_code == 200:
            return response.json()[0]
        else:
            print("UUID API error")

    except Exception as e:
        print(f"Failed to call UUID API: {e}")

    return None
def create_error_log(error_message):
    uuid = generate_uuid()

    if uuid:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"error_log_{timestamp}_{uuid}.txt"

        with open(filename, "w") as file:
            file.write(f"[{timestamp}] ERROR: {error_message}\n")

        print(f"Error log saved as: {filename}")

    else:
        print("Could not create error log - UUID not available.")


# Example usage
try:
    # Simulate an error
    result = 10 / 0

except Exception as e:
    create_error_log(str(e))