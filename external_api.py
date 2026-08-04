import logging
import requests

class UUIDService:

    def get_uuid(self):
        try:
            response = requests.get("https://www.uuidtools.com/api/generate/v1")
            # response = requests.get("https://www.youtube.com")
            response.raise_for_status()
            uuid_list = response.json()
            return uuid_list[0] if uuid_list else "unknown_uuid"
        except Exception as e:
            logging.error(
                f"UUID generation failed: {str(e)}",
                extra={"uuid": "unknown_uuid"},
            )
            return "unknown_uuid"
# Example Usage
if __name__ == "__main__":
    service = UUIDService()
    uuid = service.get_uuid()
    print("Generated UUID:", uuid)

