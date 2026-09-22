from test_admin import admin_headers
from test_auth import register


def test_student_can_request_a_new_school(client):
    headers = {"Authorization": f"Bearer {register(client).json()['access_token']}"}
    response = client.post(
        "/api/schools",
        json={"name": "Kirehe Secondary School", "district": "Kirehe", "province": "Eastern"},
        headers=headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Kirehe Secondary School"
    assert data["is_approved"] is False


def test_unapproved_school_does_not_appear_in_the_public_list(client):
    headers = {"Authorization": f"Bearer {register(client).json()['access_token']}"}
    client.post(
        "/api/schools",
        json={"name": "Kirehe Secondary School", "district": "Kirehe", "province": "Eastern"},
        headers=headers,
    )

    names = [s["name"] for s in client.get("/api/schools").json()]
    assert "Kirehe Secondary School" not in names


def test_requesting_the_same_school_twice_returns_the_existing_one(client):
    headers = {"Authorization": f"Bearer {register(client).json()['access_token']}"}
    payload = {"name": "Kirehe Secondary School", "district": "Kirehe", "province": "Eastern"}

    first = client.post("/api/schools", json=payload, headers=headers).json()
    second = client.post("/api/schools", json=payload, headers=headers).json()
    assert first["id"] == second["id"]


def test_student_can_create_a_profile_against_their_own_pending_school(client):
    headers = {"Authorization": f"Bearer {register(client).json()['access_token']}"}
    school = client.post(
        "/api/schools",
        json={"name": "Kirehe Secondary School", "district": "Kirehe", "province": "Eastern"},
        headers=headers,
    ).json()

    response = client.post(
        "/api/students/me",
        json={"full_name": "Aline Uwase", "school_id": school["id"], "age_range": "15-16"},
        headers=headers,
    )
    assert response.status_code == 201


def test_requesting_a_school_requires_authentication(client):
    response = client.post(
        "/api/schools", json={"name": "Kirehe Secondary School", "district": "Kirehe", "province": "Eastern"}
    )
    assert response.status_code == 401


def test_non_admin_cannot_list_schools_for_review(client):
    headers = {"Authorization": f"Bearer {register(client).json()['access_token']}"}
    response = client.get("/api/admin/schools", headers=headers)
    assert response.status_code == 403


def test_admin_can_approve_a_requested_school(client, db_session):
    student_headers = {"Authorization": f"Bearer {register(client).json()['access_token']}"}
    school = client.post(
        "/api/schools",
        json={"name": "Kirehe Secondary School", "district": "Kirehe", "province": "Eastern"},
        headers=student_headers,
    ).json()

    headers, _ = admin_headers(client, db_session)

    pending = client.get("/api/admin/schools?pending_only=true", headers=headers).json()
    assert any(s["id"] == school["id"] for s in pending)

    approve = client.patch(f"/api/admin/schools/{school['id']}/approve", headers=headers)
    assert approve.status_code == 200
    assert approve.json()["is_approved"] is True

    names = [s["name"] for s in client.get("/api/schools").json()]
    assert "Kirehe Secondary School" in names


def test_admin_can_reject_an_unused_school(client, db_session):
    student_headers = {"Authorization": f"Bearer {register(client).json()['access_token']}"}
    school = client.post(
        "/api/schools",
        json={"name": "Kirehe Secondary School", "district": "Kirehe", "province": "Eastern"},
        headers=student_headers,
    ).json()

    headers, _ = admin_headers(client, db_session)

    response = client.delete(f"/api/admin/schools/{school['id']}", headers=headers)
    assert response.status_code == 204

    remaining = client.get("/api/admin/schools", headers=headers).json()
    assert not any(s["id"] == school["id"] for s in remaining)


def test_admin_cannot_reject_a_school_already_in_use(client, db_session):
    student_headers = {"Authorization": f"Bearer {register(client).json()['access_token']}"}
    school = client.post(
        "/api/schools",
        json={"name": "Kirehe Secondary School", "district": "Kirehe", "province": "Eastern"},
        headers=student_headers,
    ).json()
    client.post(
        "/api/students/me",
        json={"full_name": "Aline Uwase", "school_id": school["id"], "age_range": "15-16"},
        headers=student_headers,
    )

    headers, _ = admin_headers(client, db_session)

    response = client.delete(f"/api/admin/schools/{school['id']}", headers=headers)
    assert response.status_code == 409
