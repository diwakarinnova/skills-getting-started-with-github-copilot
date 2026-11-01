from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from src.app import activities, app


@pytest.fixture(autouse=True)
def restore_activities():
    original_activities = deepcopy(activities)
    try:
        yield
    finally:
        activities.clear()
        activities.update(original_activities)


@pytest.fixture
def client():
    return TestClient(app)


def test_get_activities_returns_activity_data(client):
    # Arrange
    activity_name = "Basketball Club"
    expected_activity = {
        "description": "Practice basketball skills and play team games",
        "schedule": "Tuesdays, 3:30 PM - 5:00 PM",
        "max_participants": 20,
        "participants": [],
    }

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert response.json()[activity_name] == expected_activity


def test_signup_adds_participant(client):
    # Arrange
    activity_name = "Basketball Club"
    email = "new-student@mergington.edu"

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {
        "message": f"Signed up {email} for {activity_name}"
    }
    assert activities[activity_name]["participants"] == [email]


def test_signup_rejects_duplicate_participant(client):
    # Arrange
    activity_name = "Basketball Club"
    email = "existing-student@mergington.edu"
    activities[activity_name]["participants"].append(email)

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 400
    assert activities[activity_name]["participants"] == [email]


def test_signup_returns_not_found_for_unknown_activity(client):
    # Arrange
    activity_name = "Unknown Club"

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": "student@mergington.edu"},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_removes_only_requested_participant(client):
    # Arrange
    activity_name = "Basketball Club"
    email = "student-to-remove@mergington.edu"
    remaining_email = "remaining-student@mergington.edu"
    activities[activity_name]["participants"].extend([email, remaining_email])

    # Act
    response = client.delete(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {
        "message": f"Unregistered {email} from {activity_name}"
    }
    assert activities[activity_name]["participants"] == [remaining_email]


def test_unregister_returns_not_found_for_unknown_activity(client):
    # Arrange
    activity_name = "Unknown Club"

    # Act
    response = client.delete(
        f"/activities/{activity_name}/signup",
        params={"email": "student@mergington.edu"},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_returns_not_found_for_unregistered_participant(client):
    # Arrange
    activity_name = "Basketball Club"
    email = "not-registered@mergington.edu"

    # Act
    response = client.delete(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Student is not signed up for this activity"
    assert activities[activity_name]["participants"] == []