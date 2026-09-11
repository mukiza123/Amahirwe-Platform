from app.models.school import School

from test_auth import register


def make_school(db_session, name="Nyagatare Secondary School"):
    school = School(name=name, district="Nyagatare", province="Eastern")
    db_session.add(school)
    db_session.commit()
    db_session.refresh(school)
    return school


def student_headers(client):
    token = register(client).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_create_profile_requires_an_existing_school(client):
    headers = student_headers(client)
    response = client.post(
        "/api/students/me",
        json={"full_name": "Aline Uwase", "school_id": "does-not-exist", "age_range": "15-16"},
        headers=headers,
    )
    assert response.status_code == 404


def test_student_can_create_and_fetch_own_profile(client, db_session):
    school = make_school(db_session)
    headers = student_headers(client)

    create_response = client.post(
        "/api/students/me",
        json={"full_name": "Aline Uwase", "school_id": school.id, "age_range": "15-16"},
        headers=headers,
    )
    assert create_response.status_code == 201
    assert create_response.json()["school_id"] == school.id

    read_response = client.get("/api/students/me", headers=headers)
    assert read_response.status_code == 200
    assert read_response.json()["full_name"] == "Aline Uwase"


def test_cannot_create_a_second_profile(client, db_session):
    school = make_school(db_session)
    headers = student_headers(client)
    payload = {"full_name": "Aline Uwase", "school_id": school.id, "age_range": "15-16"}

    client.post("/api/students/me", json=payload, headers=headers)
    second = client.post("/api/students/me", json=payload, headers=headers)
    assert second.status_code == 409


def test_only_students_can_create_a_profile(client, db_session):
    school = make_school(db_session)
    token = register(client, email="teacher@example.com", role="teacher").json()["access_token"]
    response = client.post(
        "/api/students/me",
        json={"full_name": "A Teacher", "school_id": school.id, "age_range": "15-16"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403


def test_reading_profile_before_creating_one_returns_404(client):
    headers = student_headers(client)
    response = client.get("/api/students/me", headers=headers)
    assert response.status_code == 404


def test_student_can_update_own_profile(client, db_session):
    school = make_school(db_session)
    headers = student_headers(client)
    client.post(
        "/api/students/me",
        json={"full_name": "Aline Uwase", "school_id": school.id, "age_range": "15-16"},
        headers=headers,
    )

    response = client.patch("/api/students/me", json={"age_range": "17-19"}, headers=headers)
    assert response.status_code == 200
    assert response.json()["age_range"] == "17-19"


def test_another_student_cannot_view_someone_elses_profile(client, db_session):
    school = make_school(db_session)
    headers_a = student_headers(client)
    profile = client.post(
        "/api/students/me",
        json={"full_name": "Aline Uwase", "school_id": school.id, "age_range": "15-16"},
        headers=headers_a,
    ).json()

    token_b = register(client, email="other@example.com").json()["access_token"]
    response = client.get(f"/api/students/{profile['id']}", headers={"Authorization": f"Bearer {token_b}"})
    assert response.status_code == 403
