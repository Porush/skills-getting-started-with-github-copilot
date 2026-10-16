from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from src import app as app_module


@pytest.fixture
def activities(monkeypatch):
    test_activities = {
        "Chess Club": {
            "description": "Play chess",
            "schedule": "Fridays",
            "max_participants": 2,
            "participants": ["student@example.com"],
        }
    }
    monkeypatch.setattr(app_module, "activities", deepcopy(test_activities))
    return app_module.activities


@pytest.fixture
def client(activities):
    return TestClient(app_module.app)


def test_root_redirects_to_static_index(client):
    # Arrange

    # Act
    response = client.get("/", follow_redirects=False)

    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_activities_without_caching(client, activities):
    # Arrange

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert response.json() == activities
    assert response.headers["cache-control"] == "no-store"


def test_signup_adds_student_to_activity(client, activities):
    # Arrange
    email = "new.student@example.com"

    # Act
    response = client.post(
        "/activities/Chess Club/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {
        "message": f"Signed up {email} for Chess Club"
    }
    assert email in activities["Chess Club"]["participants"]


def test_signup_returns_404_for_unknown_activity(client):
    # Arrange
    email = "new.student@example.com"

    # Act
    response = client.post(
        "/activities/Unknown Club/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_signup_returns_400_when_student_is_already_signed_up(client):
    # Arrange
    email = "student@example.com"

    # Act
    response = client.post(
        "/activities/Chess Club/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 400
    assert response.json() == {
        "detail": "Student already signed up for this activity"
    }


def test_unregister_removes_student_from_activity(client, activities):
    # Arrange
    email = "student@example.com"

    # Act
    response = client.delete(
        "/activities/Chess Club/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {
        "message": f"Unregistered {email} from Chess Club"
    }
    assert email not in activities["Chess Club"]["participants"]


def test_unregister_returns_404_for_unknown_activity(client):
    # Arrange
    email = "student@example.com"

    # Act
    response = client.delete(
        "/activities/Unknown Club/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_unregister_returns_404_when_student_is_not_signed_up(client):
    # Arrange
    email = "not.signed.up@example.com"

    # Act
    response = client.delete(
        "/activities/Chess Club/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 404
    assert response.json() == {
        "detail": "Student is not signed up for this activity"
    }
