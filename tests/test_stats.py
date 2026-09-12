from test_admin import admin_headers
from test_assessments import answers_favouring
from test_auth import register
from test_guardians import make_teacher_with_student
from test_mentors import mentor_headers
from test_opportunities import OPP_PAYLOAD, provider_headers, verify
from test_students import make_school
from test_teachers import teacher_headers


def test_teacher_overview_counts_are_real(client, db_session):
    school, teacher, student = make_teacher_with_student(client, db_session)
    response = client.get("/api/teachers/me/overview", headers=teacher)
    assert response.status_code == 200
    data = response.json()
    assert data["student_count"] == 1
    assert data["pending_match_count"] == 0
    assert data["students_with_assessment_count"] == 0
    assert data["students"][0]["full_name"] == "Jean Claude"
    assert data["students"][0]["top_talent_area"] is None


def test_teacher_overview_reflects_completed_assessment(client, db_session):
    school = make_school(db_session)
    student_token = register(client, email="student@example.com").json()["access_token"]
    student_headers_ = {"Authorization": f"Bearer {student_token}"}
    client.post(
        "/api/students/me",
        json={"full_name": "Aline Uwase", "school_id": school.id, "age_range": "15-16"},
        headers=student_headers_,
    )
    client.post(
        "/api/assessments",
        json={"language": "rw", "answers": answers_favouring("a", count=6)},
        headers=student_headers_,
    )

    teacher = teacher_headers(client)
    client.post("/api/teachers/me", json={"school_id": school.id}, headers=teacher)

    response = client.get("/api/teachers/me/overview", headers=teacher)
    data = response.json()
    assert data["students_with_assessment_count"] == 1
    assert data["students"][0]["top_talent_area"] == "technology"


def test_mentor_overview_counts_expertise_and_matches(client, db_session):
    headers = mentor_headers(client)
    client.post(
        "/api/mentors/me",
        json={"district": "Nyagatare", "expertise_areas": ["technology", "leadership"]},
        headers=headers,
    )
    response = client.get("/api/mentors/me/overview", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["expertise_count"] == 2
    assert data["approved_mentee_count"] == 0
    assert data["pending_request_count"] == 0


def test_opportunity_overview_counts_real_postings(client, db_session):
    headers = provider_headers(client)
    verify(db_session, "provider@example.com")
    client.post("/api/opportunities", json=OPP_PAYLOAD, headers=headers)

    response = client.get("/api/opportunities/mine/overview", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total_count"] == 1
    assert data["active_count"] == 1
    assert data["by_talent_area"] == {"technology": 1}


def test_admin_overview_reflects_real_platform_state(client, db_session):
    headers, admin = admin_headers(client, db_session)
    register(client, email="student@example.com", role="student")
    register(client, email="mentor@example.com", role="mentor")

    response = client.get("/api/admin/overview", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total_users"] == 3
    assert data["users_by_role"]["student"] == 1
    assert data["users_by_role"]["mentor"] == 1
    assert data["pending_verification_count"] == 1
    assert len(data["signups_last_14_days"]) == 14
    assert sum(d["count"] for d in data["signups_last_14_days"]) == 3


def test_non_provider_cannot_read_opportunity_overview(client):
    token = register(client, email="student@example.com").json()["access_token"]
    response = client.get("/api/opportunities/mine/overview", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403
