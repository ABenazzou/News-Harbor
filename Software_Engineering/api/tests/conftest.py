from fastapi.testclient import TestClient
from main import app  
import pytest


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client
        