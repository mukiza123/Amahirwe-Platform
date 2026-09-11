from app.services.assessment_bank import QUESTION_BANK

from test_auth import register
from test_students import make_school, student_headers


def create_student_and_headers(client, db_session, email="student@example.com"):
    school = make_school(db_session)
    token = register(client, email=email).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    client.post(
        "/api/students/me",
        json={"full_name": "Aline Uwase", "school_id": school.id, "age_range": "15-16"},
        headers=headers,
    )
    return headers


def answers_favouring(talent_area_choice_letter, count=6):
    """Build `count` answers whose choice always ends in the given letter
    (e.g. "a"), across the first `count` questions in the bank."""
    answers = []
    for question in QUESTION_BANK[:count]:
        choice_id = f"{question['id']}{talent_area_choice_letter}"
        answers.append({"question_id": question["id"], "choice_id": choice_id})
    return answers


def test_questions_endpoint_requires_a_student(client):
    response = client.get("/api/assessments/questions")
    assert response.status_code == 401


def test_questions_endpoint_returns_the_question_bank(client, db_session):
    headers = create_student_and_headers(client, db_session)
    response = client.get("/api/assessments/questions", headers=headers)
    assert response.status_code == 200
    assert len(response.json()) == len(QUESTION_BANK)
    assert response.json()[0]["choices"]


def test_submit_assessment_without_a_profile_fails(client):
    token = register(client).json()["access_token"]
    response = client.post(
        "/api/assessments",
        json={"language": "rw", "answers": [{"question_id": "q1", "choice_id": "q1a"}]},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 404


def test_submit_assessment_rejects_unknown_choice(client, db_session):
    headers = create_student_and_headers(client, db_session)
    response = client.post(
        "/api/assessments",
        json={"language": "rw", "answers": [{"question_id": "q1", "choice_id": "not-a-real-choice"}]},
        headers=headers,
    )
    assert response.status_code == 400


def test_submit_assessment_computes_and_ranks_results(client, db_session):
    headers = create_student_and_headers(client, db_session)

    # "a" is technology on every question in the bank, so answering "a"
    # everywhere should make technology the clear top result.
    payload = {"language": "rw", "answers": answers_favouring("a", count=len(QUESTION_BANK))}
    response = client.post("/api/assessments", json=payload, headers=headers)

    assert response.status_code == 201
    data = response.json()
    assert data["results"][0]["talent_area"] == "technology"
    assert data["results"][0]["rank"] == 1
    assert data["results"][0]["explanation"]
    # At most the top 3 strengths are returned, not every talent area touched.
    assert len(data["results"]) <= 3


def test_list_my_assessments_only_shows_the_students_own(client, db_session):
    headers_a = create_student_and_headers(client, db_session, email="a@example.com")
    headers_b = create_student_and_headers(client, db_session, email="b@example.com")

    payload = {"language": "rw", "answers": answers_favouring("a", count=4)}
    client.post("/api/assessments", json=payload, headers=headers_a)

    response_a = client.get("/api/assessments", headers=headers_a)
    response_b = client.get("/api/assessments", headers=headers_b)

    assert len(response_a.json()) == 1
    assert len(response_b.json()) == 0


def test_a_student_cannot_read_another_students_assessment(client, db_session):
    headers_a = create_student_and_headers(client, db_session, email="a@example.com")
    headers_b = create_student_and_headers(client, db_session, email="b@example.com")

    payload = {"language": "rw", "answers": answers_favouring("a", count=4)}
    assessment = client.post("/api/assessments", json=payload, headers=headers_a).json()

    response = client.get(f"/api/assessments/{assessment['id']}", headers=headers_b)
    assert response.status_code == 403
