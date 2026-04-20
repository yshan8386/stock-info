from fastapi.testclient import TestClient
from uuid import uuid4

from app.main import app


def test_signup_sets_cookie_and_returns_user() -> None:
    suffix = uuid4().hex[:8]
    username = f"tester_{suffix}"
    phone_suffix = str(uuid4().int % 100000000).zfill(8)
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/auth/signup",
            json={
                "username": username,
                "password": "secret123",
                "password_confirm": "secret123",
                "display_name": "테스터",
                "phone": f"010{phone_suffix}",
                "email": f"{username}@example.com",
            },
        )
    assert response.status_code == 201
    assert response.json()["user"]["username"] == username
    assert "access_token" in response.cookies
