from app.models.user import User

from test_auth import register

OPP_PAYLOAD = {
    "title": "Coding Bootcamp Scholarship",
    "description": "A 6-week scholarship for students interested in software development.",
    "talent_area": "technology",
    "location": "Kigali",
}


def provider_headers(client, email="provider@example.com"):
    token = register(client, email=email, role="provider").json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def verify(db_session, email):
    user = db_session.query(User).filter(User.email == email).first()
    user.is_verified = True
    db_session.commit()


def test_unverified_provider_cannot_post_an_opportunity(client):
    headers = provider_headers(client)
    response = client.post("/api/opportunities", json=OPP_PAYLOAD, headers=headers)
    assert response.status_code == 403


def test_verified_provider_can_post_and_it_appears_publicly(client, db_session):
    headers = provider_headers(client)
    verify(db_session, "provider@example.com")

    created = client.post("/api/opportunities", json=OPP_PAYLOAD, headers=headers)
    assert created.status_code == 201
    assert created.json()["provider_name"] == "Aline Uwase"

    public_listing = client.get("/api/opportunities")
    assert public_listing.status_code == 200
    assert len(public_listing.json()) == 1


def test_public_listing_only_shows_active_opportunities(client, db_session):
    headers = provider_headers(client)
    verify(db_session, "provider@example.com")
    created = client.post("/api/opportunities", json=OPP_PAYLOAD, headers=headers).json()

    client.patch(f"/api/opportunities/{created['id']}", json={"is_active": False}, headers=headers)

    assert client.get("/api/opportunities").json() == []
    assert len(client.get("/api/opportunities/mine", headers=headers).json()) == 1


def test_provider_cannot_edit_someone_elses_opportunity(client, db_session):
    headers_a = provider_headers(client, email="a@example.com")
    verify(db_session, "a@example.com")
    created = client.post("/api/opportunities", json=OPP_PAYLOAD, headers=headers_a).json()

    headers_b = provider_headers(client, email="b@example.com")
    verify(db_session, "b@example.com")
    response = client.patch(f"/api/opportunities/{created['id']}", json={"title": "Hijacked"}, headers=headers_b)
    assert response.status_code == 403


def test_provider_can_delete_own_opportunity(client, db_session):
    headers = provider_headers(client)
    verify(db_session, "provider@example.com")
    created = client.post("/api/opportunities", json=OPP_PAYLOAD, headers=headers).json()

    response = client.delete(f"/api/opportunities/{created['id']}", headers=headers)
    assert response.status_code == 204
    assert client.get("/api/opportunities/mine", headers=headers).json() == []
