import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def user_token(client: TestClient) -> str:
    # Create a test user
    user_data = {
        "email": "todo_test@example.com",
        "password": "testpassword123",
        "username": "todo_testuser",
    }
    client.post("/api/v1/users/", json=user_data)

    # Login and get token
    login_data = {"username": user_data["email"], "password": user_data["password"]}
    response = client.post("/api/v1/login/", data=login_data)
    return response.json()["access_token"]


def test_create_todo(client: TestClient, user_token: str):
    todo_data = {
        "title": "Test Todo",
        "description": "This is a test todo item",
    }
    response = client.post(
        "/api/v1/todos/",
        json=todo_data,
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == todo_data["title"]
    assert data["description"] == todo_data["description"]
    assert "id" in data
    assert not data["completed"]


def test_read_todos(client: TestClient, user_token: str):
    # Create a todo first
    todo_data = {"title": "Test Todo for Reading"}
    client.post(
        "/api/v1/todos/",
        json=todo_data,
        headers={"Authorization": f"Bearer {user_token}"},
    )

    # Get all todos
    response = client.get(
        "/api/v1/todos/", headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert data[0]["title"] == todo_data["title"]


def test_read_todo(client: TestClient, user_token: str):
    # Create a todo first
    todo_data = {"title": "Test Todo for Reading Single"}
    create_response = client.post(
        "/api/v1/todos/",
        json=todo_data,
        headers={"Authorization": f"Bearer {user_token}"},
    )
    todo_id = create_response.json()["id"]

    # Get the specific todo
    response = client.get(
        f"/api/v1/todos/{todo_id}", headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == todo_id
    assert data["title"] == todo_data["title"]


def test_update_todo(client: TestClient, user_token: str):
    # Create a todo first
    todo_data = {"title": "Original Title"}
    create_response = client.post(
        "/api/v1/todos/",
        json=todo_data,
        headers={"Authorization": f"Bearer {user_token}"},
    )
    todo_id = create_response.json()["id"]

    # Update the todo
    update_data = {"title": "Updated Title", "completed": True}
    response = client.put(
        f"/api/v1/todos/{todo_id}",
        json=update_data,
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == todo_id
    assert data["title"] == update_data["title"]
    assert data["completed"] == update_data["completed"]


def test_delete_todo(client: TestClient, user_token: str):
    # Create a todo first
    todo_data = {"title": "Todo to Delete"}
    create_response = client.post(
        "/api/v1/todos/",
        json=todo_data,
        headers={"Authorization": f"Bearer {user_token}"},
    )
    todo_id = create_response.json()["id"]

    # Delete the todo
    response = client.delete(
        f"/api/v1/todos/{todo_id}", headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 204

    # Verify the todo is deleted
    get_response = client.get(
        f"/api/v1/todos/{todo_id}", headers={"Authorization": f"Bearer {user_token}"}
    )
    assert get_response.status_code == 404
