from fastapi.testclient import TestClient
from app.core.security import create_access_token
from app.models.user import User
from app.schemas.user import UserCreate
import pytest


@pytest.mark.asyncio
async def test_create_user(client: TestClient):
    user_data = {
        "email": "test@example.com",
        "password": "testpassword123",
        "username": "testuser",
    }
    response = client.post("/api/v1/users/", json=user_data)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == user_data["email"]
    assert data["username"] == user_data["username"]
    assert "id" in data
    assert "password" not in data


@pytest.mark.asyncio
async def test_login_user(client: TestClient):
    # First create a user
    user_data = {
        "email": "login@example.com",
        "password": "loginpassword123",
        "username": "loginuser",
    }
    client.post("/api/v1/users/", json=user_data)

    # Then try to login
    login_data = {"username": user_data["email"], "password": user_data["password"]}
    response = client.post("/api/v1/login/", data=login_data)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_user_wrong_password(client: TestClient):
    login_data = {"username": "test@example.com", "password": "wrongpassword"}
    response = client.post("/api/v1/login/", data=login_data)
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user(client: TestClient):
    # First create a user and get token
    user_data = {
        "email": "current@example.com",
        "password": "currentpassword123",
        "username": "currentuser",
    }
    client.post("/api/v1/users/", json=user_data)

    login_data = {"username": user_data["email"], "password": user_data["password"]}
    login_response = client.post("/api/v1/login/", data=login_data)
    token = login_response.json()["access_token"]

    # Then try to get current user
    response = client.get(
        "/api/v1/users/me/", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == user_data["email"]
    assert data["username"] == user_data["username"]
