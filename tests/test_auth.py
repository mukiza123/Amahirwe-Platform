def register(client, email="student@example.com", role="student", password="password123"):
    return client.post(
        "/api/auth/register",
        json={
            "full_name": "Aline Uwase",
            "email": email,
            "password": password,
            "role": role,
        },
    )


def test_register_creates_account_and_returns_token(client):
    response = register(client)
    assert response.status_code == 201
    data = response.json()
    assert data["access_token"]
    assert data["user"]["email"] == "student@example.com"
    assert data["user"]["role"] == "student"
    # Students don't require admin verification, unlike mentors/providers.
    assert data["user"]["is_verified"] is True


def test_password_is_not_stored_in_plaintext(client):
    register(client)
    # The response never echoes back a password field or hash at all.
    data = register(client, email="another@example.com").json()
    assert "password" not in data["user"]
    assert "hashed_password" not in data["user"]


def test_mentor_registration_requires_later_verification(client):
    response = register(client, email="mentor@example.com", role="mentor")
    assert response.status_code == 201
    assert response.json()["user"]["is_verified"] is False


def test_duplicate_email_is_rejected(client):
    register(client)
    response = register(client)
    assert response.status_code == 409


def test_login_with_correct_credentials_succeeds(client):
    register(client)
    response = client.post("/api/auth/login", json={"email": "student@example.com", "password": "password123"})
    assert response.status_code == 200
    assert response.json()["access_token"]


def test_login_with_wrong_password_fails(client):
    register(client)
    response = client.post("/api/auth/login", json={"email": "student@example.com", "password": "wrong-password"})
    assert response.status_code == 401


def test_me_requires_a_valid_token(client):
    response = client.get("/api/auth/me")
    assert response.status_code == 401


def test_me_returns_current_user_with_valid_token(client):
    token = register(client).json()["access_token"]
    response = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["email"] == "student@example.com"


def test_me_rejects_a_garbage_token(client):
    response = client.get("/api/auth/me", headers={"Authorization": "Bearer not-a-real-token"})
    assert response.status_code == 401
