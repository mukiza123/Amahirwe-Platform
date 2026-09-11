from test_auth import register
from test_students import make_school


def teacher_headers(client, email="teacher@example.com"):
    token = register(client, email=email, role="teacher").json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_creating_profile_requires_an_existing_school(client):
    headers = teacher_headers(client)
    response = client.post("/api/teachers/me", json={"school_id": "does-not-exist"}, headers=headers)
    assert response.status_code == 404


def test_teacher_can_create_profile_and_add_a_student(client, db_session):
    school = make_school(db_session)
    headers = teacher_headers(client)

    profile = client.post("/api/teachers/me", json={"school_id": school.id}, headers=headers)
    assert profile.status_code == 201

    created = client.post(
        "/api/teachers/students",
        json={"full_name": "Jean Claude", "age_range": "12-14"},
        headers=headers,
    )
    assert created.status_code == 201
    assert created.json()["school_id"] == school.id
    assert created.json()["user_id"] is None

    listing = client.get("/api/teachers/me/students", headers=headers)
    assert listing.status_code == 200
    assert len(listing.json()) == 1
    assert listing.json()[0]["full_name"] == "Jean Claude"


def test_only_teachers_can_create_a_teacher_profile(client, db_session):
    school = make_school(db_session)
    token = register(client, email="student@example.com", role="student").json()["access_token"]
    response = client.post(
        "/api/teachers/me",
        json={"school_id": school.id},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403


def test_teacher_only_sees_students_at_their_own_school(client, db_session):
    school_a = make_school(db_session, name="School A")
    school_b = make_school(db_session, name="School B")

    headers_a = teacher_headers(client, email="teacher-a@example.com")
    client.post("/api/teachers/me", json={"school_id": school_a.id}, headers=headers_a)
    client.post("/api/teachers/students", json={"full_name": "Student A", "age_range": "12-14"}, headers=headers_a)

    headers_b = teacher_headers(client, email="teacher-b@example.com")
    client.post("/api/teachers/me", json={"school_id": school_b.id}, headers=headers_b)

    response = client.get("/api/teachers/me/students", headers=headers_b)
    assert response.status_code == 200
    assert response.json() == []


def test_creating_a_student_before_a_profile_exists_fails(client):
    headers = teacher_headers(client)
    response = client.post(
        "/api/teachers/students", json={"full_name": "Jean Claude", "age_range": "12-14"}, headers=headers
    )
    assert response.status_code == 404
