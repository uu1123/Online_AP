import requests

# Step 1: Target Interface (expected interface in your app)
class UUIDGenerator:
    def get_uuid(self):
        raise NotImplementedError("Subclasses must implement get_uuid()")


# Step 2: Adaptee (external system – UUIDTools API)
class UUIDToolsAPI:
    def fetch_uuid_v1(self):
        url = "https://www.uuidtools.com/api/generate/v1"
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # raise error if response failed
        return response.json()  # returns list like ["uuid-string"]


# Step 3: Adapter
class UUIDAdapter(UUIDGenerator):
    def __init__(self, api: UUIDToolsAPI):
        self.api = api

    def get_uuid(self):
        uuid_list = self.api.fetch_uuid_v1()
        if isinstance(uuid_list, list) and uuid_list:
            return uuid_list[0]  # return first UUID
        return None


# Step 4: Client code
if __name__ == "__main__":
    # Create the Adaptee
    api = UUIDToolsAPI()

    # Wrap it with the Adapter
    uuid_service = UUIDAdapter(api)

    # Use it through the expected interface
    generated_uuid = uuid_service.get_uuid()

    print(f"[Adapter] Generated UUID (v1): {generated_uuid}")