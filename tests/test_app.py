from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from src.app import activities, app


client = TestClient(app)


@pytest.fixture(autouse=True)
def restore_activities():
    original_activities = deepcopy(activities)
    yield
    activities.clear()
    activities.update(original_activities)


def test_root_redirects_to_static_homepage():
    response = client.get("/", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_static_homepage_is_served():
    response = client.get("/static/index.html")

    assert response.status_code == 200
    assert "<html" in response.text.lower()


def test_get_activities_returns_activity_details():
    response = client.get("/activities")

    assert response.status_code == 200
    result = response.json()
    assert result.keys() == activities.keys()
    assert result["Chess Club"] == activities["Chess Club"]


def test_signup_adds_participant_and_returns_confirmation():
    email = "student@mergington.edu"

    response = client.post(
        "/activities/Chess%20Club/signup",
        params={"email": email},
    )

    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for Chess Club"}
    assert email in activities["Chess Club"]["participants"]


def test_signup_rejects_duplicate_participant():
    email = "michael@mergington.edu"
    original_count = activities["Chess Club"]["participants"].count(email)

    response = client.post(
        "/activities/Chess%20Club/signup",
        params={"email": email},
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "Student is already signed up"}
    assert activities["Chess Club"]["participants"].count(email) == original_count


def test_signup_for_unknown_activity_returns_not_found():
    response = client.post(
        "/activities/Unknown%20Club/signup",
        params={"email": "student@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_signup_without_email_returns_validation_error():
    response = client.post("/activities/Chess%20Club/signup")

    assert response.status_code == 422
