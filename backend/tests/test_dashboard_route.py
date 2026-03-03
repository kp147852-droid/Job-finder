from fastapi.testclient import TestClient

from app.main import app


def test_dashboard_root_serves_html():
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    assert "ApplyFlow Dashboard" in response.text
