from test_auth import register


def mentor_headers(client, email="mentor@example.com"):
    token = register(client, email=email, role="mentor").json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_mentor_can_create_a_profile(client):
    headers = mentor_headers(client)
    response = client.post(
        "/api/mentors/me",
        json={"bio": "I teach robotics.", "district": "Nyagatare", "expertise_areas": ["technology", "leadership"]},
        headers=headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["district"] == "Nyagatare"
    assert set(data["expertise_areas"]) == {"technology", "leadership"}
    # Mentors start unverified regardless of profile completeness (SRS 5.5).
    assert data["is_verified"] is False


def test_unverified_mentor_is_not_listed_publicly(client, db_session):
    headers = mentor_headers(client)
    client.post(
        "/api/mentors/me",
        json={"district": "Nyagatare", "expertise_areas": ["technology"]},
        headers=headers,
    )

    student_token = register(client, email="student@example.com", role="student").json()["access_token"]
    listing = client.get("/api/mentors", headers={"Authorization": f"Bearer {student_token}"})
    assert listing.status_code == 200
    assert listing.json() == []


def test_verified_mentor_appears_in_listing(client, db_session):
    from app.models.user import User

    headers = mentor_headers(client)
    client.post(
        "/api/mentors/me",
        json={"district": "Nyagatare", "expertise_areas": ["technology"]},
        headers=headers,
    )
    mentor_user = db_session.query(User).filter(User.email == "mentor@example.com").first()
    mentor_user.is_verified = True
    db_session.commit()

    student_token = register(client, email="student@example.com", role="student").json()["access_token"]
    listing = client.get("/api/mentors", headers={"Authorization": f"Bearer {student_token}"})
    assert len(listing.json()) == 1
    assert listing.json()[0]["district"] == "Nyagatare"


def test_mentor_can_update_expertise(client):
    headers = mentor_headers(client)
    client.post(
        "/api/mentors/me",
        json={"district": "Nyagatare", "expertise_areas": ["technology"]},
        headers=headers,
    )
    response = client.patch("/api/mentors/me", json={"expertise_areas": ["art", "creativity"]}, headers=headers)
    assert response.status_code == 200
    assert set(response.json()["expertise_areas"]) == {"art", "creativity"}


def test_only_mentors_can_create_a_mentor_profile(client):
    token = register(client, email="student@example.com", role="student").json()["access_token"]
    response = client.post(
        "/api/mentors/me",
        json={"district": "Nyagatare", "expertise_areas": ["technology"]},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403
