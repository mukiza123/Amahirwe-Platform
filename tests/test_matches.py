from app.models.user import User

from test_assessments import answers_favouring
from test_auth import register
from test_mentors import mentor_headers
from test_students import make_school
from test_teachers import teacher_headers


def make_matched_student(client, db_session, email="student@example.com"):
    """A student, at a school, with a completed assessment that favours
    technology (choice letter "a" per QUESTION_BANK, same as
    test_assessments.py)."""

    school = make_school(db_session)
    token = register(client, email=email).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    client.post(
        "/api/students/me",
        json={"full_name": "Aline Uwase", "school_id": school.id, "age_range": "15-16"},
        headers=headers,
    )
    client.post(
        "/api/assessments",
        json={"language": "rw", "answers": answers_favouring("a", count=6)},
        headers=headers,
    )
    return school, headers


def make_verified_mentor(client, db_session, email="mentor@example.com", area="technology"):
    headers = mentor_headers(client, email=email)
    client.post("/api/mentors/me", json={"district": "Nyagatare", "expertise_areas": [area]}, headers=headers)
    user = db_session.query(User).filter(User.email == email).first()
    user.is_verified = True
    db_session.commit()
    return headers


def test_finding_a_mentor_requires_a_completed_assessment(client, db_session):
    school = make_school(db_session)
    token = register(client, email="student@example.com").json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    client.post(
        "/api/students/me",
        json={"full_name": "Aline Uwase", "school_id": school.id, "age_range": "15-16"},
        headers=headers,
    )
    response = client.post("/api/matches/find", headers=headers)
    assert response.status_code == 400


def test_finding_a_mentor_with_no_candidates_returns_404(client, db_session):
    school, headers = make_matched_student(client, db_session)
    response = client.post("/api/matches/find", headers=headers)
    assert response.status_code == 404


def test_student_can_request_a_match_and_it_starts_pending(client, db_session):
    school, student = make_matched_student(client, db_session)
    make_verified_mentor(client, db_session)

    response = client.post("/api/matches/find", headers=student)
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "pending"
    assert data["talent_area"] == "technology"
    # No contact details before a teacher/admin approves the match.
    assert data["mentor_contact_email"] is None
    assert data["student_contact_email"] is None


def test_teacher_outside_the_school_cannot_approve(client, db_session):
    school, student = make_matched_student(client, db_session)
    make_verified_mentor(client, db_session)
    match = client.post("/api/matches/find", headers=student).json()

    other_school = make_school(db_session, name="Another School")
    outsider = teacher_headers(client, email="outsider@example.com")
    client.post("/api/teachers/me", json={"school_id": other_school.id}, headers=outsider)

    response = client.patch(f"/api/matches/{match['id']}/approve", headers=outsider)
    assert response.status_code == 403


def test_teacher_at_the_students_school_can_approve_and_unlocks_contact(client, db_session):
    school, student = make_matched_student(client, db_session)
    make_verified_mentor(client, db_session)
    match = client.post("/api/matches/find", headers=student).json()

    teacher = teacher_headers(client)
    client.post("/api/teachers/me", json={"school_id": school.id}, headers=teacher)

    response = client.patch(f"/api/matches/{match['id']}/approve", headers=teacher)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "approved"
    assert data["mentor_contact_email"] == "mentor@example.com"
    assert data["student_contact_email"] == "student@example.com"


def test_cannot_review_the_same_match_twice(client, db_session):
    school, student = make_matched_student(client, db_session)
    make_verified_mentor(client, db_session)
    match = client.post("/api/matches/find", headers=student).json()

    teacher = teacher_headers(client)
    client.post("/api/teachers/me", json={"school_id": school.id}, headers=teacher)
    client.patch(f"/api/matches/{match['id']}/approve", headers=teacher)

    response = client.patch(f"/api/matches/{match['id']}/reject", headers=teacher)
    assert response.status_code == 409


def test_rejected_match_never_exposes_contact_details(client, db_session):
    school, student = make_matched_student(client, db_session)
    make_verified_mentor(client, db_session)
    match = client.post("/api/matches/find", headers=student).json()

    teacher = teacher_headers(client)
    client.post("/api/teachers/me", json={"school_id": school.id}, headers=teacher)
    response = client.patch(f"/api/matches/{match['id']}/reject", headers=teacher)

    assert response.status_code == 200
    assert response.json()["status"] == "rejected"
    assert response.json()["mentor_contact_email"] is None
