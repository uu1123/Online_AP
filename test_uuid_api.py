import pytest
import requests
import os
import uuid_api

# -------------------------
# Fixtures
# -------------------------

@pytest.fixture(scope="session")
def api_url():
    return "https://www.uuidtools.com/api/generate/v1"


@pytest.fixture(scope="session")
def real_uuid(api_url):
    """Call the real UUID API once and return the UUID."""
    response = requests.get(api_url)

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)
    assert len(data) > 0

    return data[0]


# -------------------------
# Tests
# -------------------------

def test_uuid_api_returns_uuid(real_uuid):
    """Verify the API returns a UUID."""
    assert real_uuid is not None
    assert isinstance(real_uuid, str)
    assert len(real_uuid) == 36

def test_generate_uuid():
    """Test generate_uuid() using the real API."""
    uuid = uuid_api.generate_uuid()

    assert uuid is not None
    assert isinstance(uuid, str)
    assert len(uuid) == 36

def test_create_error_log(tmp_path):
    """Test error log file creation."""
    os.chdir(tmp_path)
    uuid_api.create_error_log("Division by zero")
    files = list(tmp_path.glob("error_log_*.txt"))

    assert len(files) == 1

    content = files[0].read_text()

    assert "Division by zero" in content
    assert "ERROR" in content