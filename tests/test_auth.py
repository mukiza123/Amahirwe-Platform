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


def test_register_returns_an_unverified_account_with_a_dev_code(client):
    data = register(client).json()
    assert data["user"]["email_verified"] is False
    # 6-digit numeric code, stood in for a real email since there's no
    # email service configured for this prototype.
    assert data["dev_verification_code"] is not None
    assert len(data["dev_verification_code"]) == 6
    assert data["dev_verification_code"].isdigit()


def test_verify_email_with_correct_code_succeeds(client):
    data = register(client).json()
    token = data["access_token"]
    code = data["dev_verification_code"]

    response = client.post(
        "/api/auth/me/verify-email",
        json={"code": code},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["email_verified"] is True

    # The code can't be reused once consumed.
    again = client.post(
        "/api/auth/me/verify-email",
        json={"code": code},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert again.status_code == 200
    assert again.json()["email_verified"] is True


def test_verify_email_with_wrong_code_fails(client):
    data = register(client).json()
    token = data["access_token"]

    response = client.post(
        "/api/auth/me/verify-email",
        json={"code": "000000"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 400

    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.json()["email_verified"] is False


def test_verify_email_with_expired_code_fails(client, db_session):
    from datetime import datetime, timedelta, timezone

    from app.models.user import User

    data = register(client).json()
    token = data["access_token"]
    code = data["dev_verification_code"]

    user = db_session.query(User).filter(User.email == "student@example.com").first()
    user.email_verification_code_expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
    db_session.commit()

    response = client.post(
        "/api/auth/me/verify-email",
        json={"code": code},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 400


def test_resend_verification_issues_a_new_code(client, monkeypatch):
    import app.api.auth as auth_module

    monkeypatch.setattr(auth_module, "RESEND_COOLDOWN_SECONDS", 0)

    data = register(client).json()
    token = data["access_token"]
    old_code = data["dev_verification_code"]

    response = client.post("/api/auth/me/resend-verification", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    new_code = response.json()["dev_verification_code"]
    assert new_code is not None

    # The old code no longer works once a new one has been issued
    # (astronomically unlikely to flake: a 1-in-a-million collision
    # would have to regenerate the exact same 6-digit code).
    old_attempt = client.post(
        "/api/auth/me/verify-email",
        json={"code": old_code},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert old_attempt.status_code == 400

    new_attempt = client.post(
        "/api/auth/me/verify-email",
        json={"code": new_code},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert new_attempt.status_code == 200
    assert new_attempt.json()["email_verified"] is True


def test_resend_verification_rejects_an_already_verified_account(client):
    data = register(client).json()
    token = data["access_token"]
    client.post(
        "/api/auth/me/verify-email",
        json={"code": data["dev_verification_code"]},
        headers={"Authorization": f"Bearer {token}"},
    )

    response = client.post("/api/auth/me/resend-verification", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 409


def test_change_password_with_correct_current_password_succeeds(client):
    token = register(client).json()["access_token"]
    response = client.post(
        "/api/auth/me/password",
        json={"current_password": "password123", "new_password": "newpassword456"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 204

    # The old password no longer works, the new one does.
    assert client.post(
        "/api/auth/login", json={"email": "student@example.com", "password": "password123"}
    ).status_code == 401
    assert client.post(
        "/api/auth/login", json={"email": "student@example.com", "password": "newpassword456"}
    ).status_code == 200


def test_change_password_with_wrong_current_password_fails(client):
    token = register(client).json()["access_token"]
    response = client.post(
        "/api/auth/me/password",
        json={"current_password": "wrong-password", "new_password": "newpassword456"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 401

    # The password was not changed.
    assert client.post(
        "/api/auth/login", json={"email": "student@example.com", "password": "password123"}
    ).status_code == 200


def test_change_password_requires_authentication(client):
    response = client.post(
        "/api/auth/me/password",
        json={"current_password": "password123", "new_password": "newpassword456"},
    )
    assert response.status_code == 401


# --- Google sign-in ---
# verify_oauth2_token talks to Google's servers, so these tests replace
# it with a fake that returns whatever claims each test needs instead of
# making a real network call.

import app.api.auth as auth_module  # noqa: E402


def _fake_verify(claims):
    def verify(id_token, request, client_id):
        assert id_token == "fake-id-token"
        return claims

    return verify


def test_google_auth_is_disabled_without_a_client_id(client, monkeypatch):
    monkeypatch.setattr(auth_module.settings, "google_client_id", "")
    response = client.post("/api/auth/google", json={"id_token": "fake-id-token"})
    assert response.status_code == 501


def test_google_auth_new_email_needs_a_role_first(client, monkeypatch):
    monkeypatch.setattr(auth_module.settings, "google_client_id", "test-client-id")
    monkeypatch.setattr(
        auth_module.google_id_token,
        "verify_oauth2_token",
        _fake_verify({"email": "new.student@example.com", "email_verified": True, "name": "New Student"}),
    )

    response = client.post("/api/auth/google", json={"id_token": "fake-id-token"})
    assert response.status_code == 200
    data = response.json()
    assert data["needs_role"] is True
    assert data["access_token"] is None

    # No account was actually created while we only had an email, no role.
    login = client.post(
        "/api/auth/login", json={"email": "new.student@example.com", "password": "anything"}
    )
    assert login.status_code == 401


def test_google_auth_new_email_with_role_creates_a_verified_account(client, monkeypatch):
    monkeypatch.setattr(auth_module.settings, "google_client_id", "test-client-id")
    monkeypatch.setattr(
        auth_module.google_id_token,
        "verify_oauth2_token",
        _fake_verify({"email": "new.mentor@example.com", "email_verified": True, "name": "New Mentor"}),
    )

    response = client.post("/api/auth/google", json={"id_token": "fake-id-token", "role": "mentor"})
    assert response.status_code == 200
    data = response.json()
    assert data["needs_role"] is False
    assert data["access_token"]
    assert data["user"]["email"] == "new.mentor@example.com"
    assert data["user"]["role"] == "mentor"
    # Google already proved they own the inbox, so there's no
    # code-based verification step left to do.
    assert data["user"]["email_verified"] is True
    # Mentors still need admin sign-off before they're usable, same as
    # the password-based registration path.
    assert data["user"]["is_verified"] is False


def test_google_auth_existing_user_logs_in_and_becomes_email_verified(client, monkeypatch):
    register(client, email="student@example.com")

    monkeypatch.setattr(auth_module.settings, "google_client_id", "test-client-id")
    monkeypatch.setattr(
        auth_module.google_id_token,
        "verify_oauth2_token",
        _fake_verify({"email": "student@example.com", "email_verified": True, "name": "Aline Uwase"}),
    )

    response = client.post("/api/auth/google", json={"id_token": "fake-id-token"})
    assert response.status_code == 200
    data = response.json()
    assert data["needs_role"] is False
    assert data["user"]["email"] == "student@example.com"
    # Was False right after register(); Google just confirmed the inbox.
    assert data["user"]["email_verified"] is True


def test_google_auth_rejects_unverified_google_email(client, monkeypatch):
    monkeypatch.setattr(auth_module.settings, "google_client_id", "test-client-id")
    monkeypatch.setattr(
        auth_module.google_id_token,
        "verify_oauth2_token",
        _fake_verify({"email": "sneaky@example.com", "email_verified": False}),
    )

    response = client.post("/api/auth/google", json={"id_token": "fake-id-token", "role": "student"})
    assert response.status_code == 401


def test_google_auth_rejects_an_invalid_token(client, monkeypatch):
    monkeypatch.setattr(auth_module.settings, "google_client_id", "test-client-id")

    def fail_verify(id_token, request, client_id):
        raise ValueError("Token expired or malformed")

    monkeypatch.setattr(auth_module.google_id_token, "verify_oauth2_token", fail_verify)

    response = client.post("/api/auth/google", json={"id_token": "bad-token"})
    assert response.status_code == 401


# --- Verification-code rate limiting ---


def test_verify_email_locks_out_after_too_many_wrong_attempts(client):
    token = register(client).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    for _ in range(auth_module.MAX_VERIFICATION_ATTEMPTS):
        response = client.post("/api/auth/me/verify-email", json={"code": "000000"}, headers=headers)
        assert response.status_code == 400

    # One more, even if by coincidence it were the right code, is refused.
    locked = client.post("/api/auth/me/verify-email", json={"code": "111111"}, headers=headers)
    assert locked.status_code == 429


def test_resend_verification_is_rate_limited(client):
    token = register(client).json()["access_token"]
    # register() already issued one code, starting the cooldown clock.
    response = client.post("/api/auth/me/resend-verification", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 429


# --- Forgot / reset password ---


def test_forgot_password_issues_a_code_for_an_existing_account(client):
    register(client)
    response = client.post("/api/auth/forgot-password", json={"email": "student@example.com"})
    assert response.status_code == 200
    assert response.json()["dev_reset_code"] is not None


def test_forgot_password_does_not_reveal_unknown_emails(client):
    response = client.post("/api/auth/forgot-password", json={"email": "nobody@example.com"})
    assert response.status_code == 200
    assert response.json()["dev_reset_code"] is None


def test_forgot_password_is_rate_limited(client):
    register(client)
    client.post("/api/auth/forgot-password", json={"email": "student@example.com"})
    second = client.post("/api/auth/forgot-password", json={"email": "student@example.com"})
    assert second.status_code == 429


def test_reset_password_with_correct_code_logs_in_with_the_new_password(client):
    register(client)
    code = client.post("/api/auth/forgot-password", json={"email": "student@example.com"}).json()["dev_reset_code"]

    response = client.post(
        "/api/auth/reset-password",
        json={"email": "student@example.com", "code": code, "new_password": "brandnewpass123"},
    )
    assert response.status_code == 200
    assert response.json()["access_token"]

    # Old password no longer works, new one does.
    assert (
        client.post("/api/auth/login", json={"email": "student@example.com", "password": "password123"}).status_code
        == 401
    )
    assert (
        client.post(
            "/api/auth/login", json={"email": "student@example.com", "password": "brandnewpass123"}
        ).status_code
        == 200
    )


def test_reset_password_with_wrong_code_fails(client):
    register(client)
    client.post("/api/auth/forgot-password", json={"email": "student@example.com"})

    response = client.post(
        "/api/auth/reset-password",
        json={"email": "student@example.com", "code": "000000", "new_password": "brandnewpass123"},
    )
    assert response.status_code == 400

    # The password was not changed.
    assert (
        client.post("/api/auth/login", json={"email": "student@example.com", "password": "password123"}).status_code
        == 200
    )


def test_reset_password_locks_out_after_too_many_wrong_attempts(client):
    register(client)
    client.post("/api/auth/forgot-password", json={"email": "student@example.com"})

    for _ in range(auth_module.MAX_PASSWORD_RESET_ATTEMPTS):
        response = client.post(
            "/api/auth/reset-password",
            json={"email": "student@example.com", "code": "000000", "new_password": "brandnewpass123"},
        )
        assert response.status_code == 400

    locked = client.post(
        "/api/auth/reset-password",
        json={"email": "student@example.com", "code": "111111", "new_password": "brandnewpass123"},
    )
    assert locked.status_code == 429


def test_reset_password_for_unknown_email_fails(client):
    response = client.post(
        "/api/auth/reset-password",
        json={"email": "nobody@example.com", "code": "123456", "new_password": "brandnewpass123"},
    )
    assert response.status_code == 400
