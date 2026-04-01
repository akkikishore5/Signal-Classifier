import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../app"))

import pytest
from app import create_app
from models import db as _db

VALID_SIGNAL = {
    "frequency_mhz": 1575.42,
    "bandwidth_mhz": 2.0,
    "signal_strength_dbm": -128.0,
    "modulation": "BPSK",
    "latitude": 38.8977,
    "longitude": -77.0365,
}


@pytest.fixture
def app():
    flask_app = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:"})
    with flask_app.app_context():
        yield flask_app
        _db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json()["status"] == "ok"


def test_create_signal(client):
    response = client.post("/signals", json=VALID_SIGNAL)
    assert response.status_code == 201
    data = response.get_json()
    assert data["frequency_mhz"] == 1575.42
    assert data["modulation"] == "BPSK"
    assert data["wavelength_m"] is not None


def test_wavelength_auto_calculated(client):
    response = client.post("/signals", json=VALID_SIGNAL)
    data = response.get_json()
    expected = 3e8 / (1575.42 * 1e6)
    assert abs(data["wavelength_m"] - expected) < 1e-6


def test_create_signal_missing_fields(client):
    response = client.post("/signals", json={"frequency_mhz": 1575.42})
    assert response.status_code == 400
    assert "fields" in response.get_json()


def test_list_signals_empty(client):
    response = client.get("/signals")
    assert response.status_code == 200
    assert response.get_json() == []


def test_list_signals_after_create(client):
    client.post("/signals", json=VALID_SIGNAL)
    client.post("/signals", json={**VALID_SIGNAL, "frequency_mhz": 9500.0})
    response = client.get("/signals")
    assert len(response.get_json()) == 2


def test_get_signal(client):
    client.post("/signals", json=VALID_SIGNAL)
    response = client.get("/signals/1")
    assert response.status_code == 200
    assert response.get_json()["id"] == 1


def test_get_signal_not_found(client):
    response = client.get("/signals/999")
    assert response.status_code == 404


def test_classify_signal(client):
    client.post("/signals", json=VALID_SIGNAL)
    response = client.post("/signals/1/classify")
    assert response.status_code == 200
    data = response.get_json()
    assert data["classification"] == "GPS L1"
    assert data["confidence_score"] >= 70.0
    assert data["status"] == "HIGH CONFIDENCE"


def test_classify_persists_result(client):
    client.post("/signals", json=VALID_SIGNAL)
    client.post("/signals/1/classify")
    response = client.get("/signals/1")
    data = response.get_json()
    assert data["classification"] == "GPS L1"
    assert data["confidence_score"] is not None


def test_delete_signal(client):
    client.post("/signals", json=VALID_SIGNAL)
    response = client.delete("/signals/1")
    assert response.status_code == 200
    assert client.get("/signals/1").status_code == 404
