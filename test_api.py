import sys
from pathlib import Path

APP_DIR = Path(__file__).parent / "venv"
sys.path.insert(0, str(APP_DIR))

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_home_endpoint():
    response = client.get("/")

    assert response.status_code == 200

    data = response.json()

    assert data["message"] == "Pragma CAD Engine is running"
    assert data["status"] == "online"
    assert data["version"] == "0.3.0"


def test_health_endpoint():
    response = client.get("/health")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "healthy"
    assert data["service"] == "pragma-cad-engine"


def test_print_endpoint_rejects_non_stl():
    response = client.post(
        "/analyze/print",
        files={
            "file": (
                "invalid_model.obj",
                b"This is not an STL file",
                "application/octet-stream",
            )
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Only STL files are supported currently."
    )

def test_print_endpoint_rejects_empty_file():
    response = client.post(
        "/analyze/print",
        files={
            "file": (
                "empty_model.stl",
                b"",
                "application/octet-stream",
            )
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Uploaded file is empty."

def test_print_endpoint_rejects_oversized_file():
    oversized_file = b"A" * (25 * 1024 * 1024 + 1)

    response = client.post(
        "/analyze/print",
        files={
            "file": (
                "large_model.stl",
                oversized_file,
                "application/octet-stream",
            )
        },
    )

    assert response.status_code == 413
    assert response.json()["detail"] == (
        "File size exceeds the 25 MB limit."
    )

def test_stl_endpoint_rejects_corrupted_file():
    response = client.post(
        "/analyze/stl",
        files={
            "file": (
                "broken.stl",
                b"This is not valid STL geometry",
                "application/octet-stream",
            )
        },
    )

    assert response.status_code == 400