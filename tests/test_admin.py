from app.core.security import hash_password
from app.models.user import User, UserRole

from test_auth import register

ADMIN_PASSWORD = "password123"


def admin_headers(client, db_session, email="admin@example.com"):
    """Admins aren't self-registrable (SRS 5.5: seeded by the platform),
    so tests create one directly and log in to get a real token."""

    admin = User(
        full_name="Admin User",
        email=email,
        hashed_password=hash_password(ADMIN_PASSWORD),
        role=UserRole.ADMIN,
        is_verified=True,
    )
    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)

    token = client.post("/api/auth/login", json={"email": email, "password": ADMIN_PASSWORD}).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}, admin


def test_registering_as_admin_is_rejected(client):
    response = client.post(
        "/api/auth/register",
        json={"full_name": "Sneaky", "email": "sneaky@example.com", "password": "password123", "role": "admin"},
    )
    assert response.status_code == 422


def test_non_admin_cannot_list_users(client):
    token = register(client, email="student@example.com").json()["access_token"]
    response = client.get("/api/admin/users", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403


def test_admin_can_list_and_filter_users(client, db_session):
    headers, _ = admin_headers(client, db_session)
    register(client, email="teacher@example.com", role="teacher")

    all_users = client.get("/api/admin/users", headers=headers)
    assert len(all_users.json()) == 2  # admin + teacher

    teachers_only = client.get("/api/admin/users?role=teacher", headers=headers)
    assert len(teachers_only.json()) == 1
    assert teachers_only.json()[0]["email"] == "teacher@example.com"


def test_admin_can_verify_a_mentor(client, db_session):
    headers, _ = admin_headers(client, db_session)
    mentor_id = register(client, email="mentor@example.com", role="mentor").json()["user"]["id"]

    response = client.patch(f"/api/admin/users/{mentor_id}/verify", headers=headers)
    assert response.status_code == 200
    assert response.json()["is_verified"] is True

    audit = client.get("/api/admin/audit-log", headers=headers)
    assert any(entry["action"] == "user_verified" for entry in audit.json())


def test_admin_can_deactivate_and_reactivate_a_user(client, db_session):
    headers, _ = admin_headers(client, db_session)
    user_id = register(client, email="student@example.com").json()["user"]["id"]

    deactivated = client.patch(f"/api/admin/users/{user_id}/deactivate", headers=headers)
    assert deactivated.status_code == 200
    assert deactivated.json()["is_active"] is False

    login_attempt = client.post(
        "/api/auth/login", json={"email": "student@example.com", "password": "password123"}
    )
    assert login_attempt.status_code == 403

    reactivated = client.patch(f"/api/admin/users/{user_id}/activate", headers=headers)
    assert reactivated.json()["is_active"] is True


def test_admin_cannot_deactivate_their_own_account(client, db_session):
    headers, admin = admin_headers(client, db_session)
    response = client.patch(f"/api/admin/users/{admin.id}/deactivate", headers=headers)
    assert response.status_code == 400


def test_notifications_are_created_on_verify(client, db_session):
    headers, _ = admin_headers(client, db_session)
    mentor = register(client, email="mentor@example.com", role="mentor").json()
    mentor_headers_ = {"Authorization": f"Bearer {mentor['access_token']}"}

    client.patch(f"/api/admin/users/{mentor['user']['id']}/verify", headers=headers)

    notifications = client.get("/api/notifications/me", headers=mentor_headers_)
    assert notifications.status_code == 200
    assert len(notifications.json()) == 1
    assert "verified" in notifications.json()[0]["message"]
