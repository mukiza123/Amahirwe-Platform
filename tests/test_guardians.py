from test_auth import register
from test_students import make_school
from test_teachers import teacher_headers


def parent_headers(client, email="parent@example.com"):
    token = register(client, email=email, role="parent").json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def make_teacher_with_student(client, db_session, teacher_email="teacher@example.com"):
    school = make_school(db_session)
    teacher = teacher_headers(client, email=teacher_email)
    client.post("/api/teachers/me", json={"school_id": school.id}, headers=teacher)
    student = client.post(
        "/api/teachers/students", json={"full_name": "Jean Claude", "age_range": "12-14"}, headers=teacher
    ).json()
    return school, teacher, student


def test_linking_an_unregistered_email_fails(client, db_session):
    _, teacher, student = make_teacher_with_student(client, db_session)
    response = client.post(
        f"/api/teachers/students/{student['id']}/guardians",
        json={"guardian_email": "nobody@example.com"},
        headers=teacher,
    )
    assert response.status_code == 404


def test_linking_a_non_parent_role_fails(client, db_session):
    _, teacher, student = make_teacher_with_student(client, db_session)
    register(client, email="student2@example.com", role="student")
    response = client.post(
        f"/api/teachers/students/{student['id']}/guardians",
        json={"guardian_email": "student2@example.com"},
        headers=teacher,
    )
    assert response.status_code == 404


def test_teacher_can_link_a_guardian(client, db_session):
    _, teacher, student = make_teacher_with_student(client, db_session)
    register(client, email="parent@example.com", role="parent")

    response = client.post(
        f"/api/teachers/students/{student['id']}/guardians",
        json={"guardian_email": "parent@example.com"},
        headers=teacher,
    )
    assert response.status_code == 201
    assert response.json()["guardian_email"] == "parent@example.com"


def test_linking_the_same_guardian_twice_fails(client, db_session):
    _, teacher, student = make_teacher_with_student(client, db_session)
    register(client, email="parent@example.com", role="parent")
    payload = {"guardian_email": "parent@example.com"}

    client.post(f"/api/teachers/students/{student['id']}/guardians", json=payload, headers=teacher)
    second = client.post(f"/api/teachers/students/{student['id']}/guardians", json=payload, headers=teacher)
    assert second.status_code == 409


def test_teacher_cannot_link_guardian_for_another_schools_student(client, db_session):
    _, teacher_a, student = make_teacher_with_student(client, db_session, teacher_email="teacher-a@example.com")
    _, teacher_b, _ = make_teacher_with_student(client, db_session, teacher_email="teacher-b@example.com")
    register(client, email="parent@example.com", role="parent")

    response = client.post(
        f"/api/teachers/students/{student['id']}/guardians",
        json={"guardian_email": "parent@example.com"},
        headers=teacher_b,
    )
    assert response.status_code == 404


def test_parent_sees_no_children_before_being_linked(client):
    parent = parent_headers(client)
    response = client.get("/api/parents/me/children", headers=parent)
    assert response.status_code == 200
    assert response.json() == []


def test_parent_sees_real_linked_child_data(client, db_session):
    _, teacher, student = make_teacher_with_student(client, db_session)
    parent = parent_headers(client)
    client.post(
        f"/api/teachers/students/{student['id']}/guardians",
        json={"guardian_email": "parent@example.com"},
        headers=teacher,
    )

    response = client.get("/api/parents/me/children", headers=parent)
    assert response.status_code == 200
    children = response.json()
    assert len(children) == 1
    assert children[0]["full_name"] == "Jean Claude"
    assert children[0]["has_completed_assessment"] is False
    assert children[0]["top_talents"] == []


def test_parent_does_not_see_unlinked_students(client, db_session):
    _, teacher, student = make_teacher_with_student(client, db_session)
    parent = parent_headers(client, email="other-parent@example.com")

    response = client.get("/api/parents/me/children", headers=parent)
    assert response.json() == []
