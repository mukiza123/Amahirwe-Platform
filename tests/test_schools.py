from test_students import make_school


def test_list_schools_is_public_and_sorted(client, db_session):
    make_school(db_session, name="Zebra School")
    make_school(db_session, name="Alpha School")

    response = client.get("/api/schools")
    assert response.status_code == 200
    names = [s["name"] for s in response.json()]
    assert names == ["Alpha School", "Zebra School"]
