import pytest
from fastapi.testclient import TestClient
from app import app, API_TOKEN

client = TestClient(app)

def test_healthcheck():
    response = client.get("/healthcheck")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_scrape_unauthorized():
    response = client.post("/scrape")
    assert response.status_code == 422  # missing header -> 422 because token not provided

def test_scrape_authorized():
    headers = {"token": API_TOKEN}
    response = client.post("/scrape", headers=headers)
    assert response.status_code == 200
    assert "Scraping initiated" in response.json()["message"]