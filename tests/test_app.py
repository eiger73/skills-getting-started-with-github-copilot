import copy
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Ensure src is on the import path for tests
ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = ROOT / "src"
sys.path.append(str(SRC_PATH))

import app as app_module  # noqa: E402


@pytest.fixture()
def client():
  return TestClient(app_module.app)


@pytest.fixture(autouse=True)
def restore_activities():
  """Snapshot activities and restore after each test."""
  snapshot = copy.deepcopy(app_module.activities)
  try:
    yield
  finally:
    app_module.activities.clear()
    app_module.activities.update(snapshot)


def test_get_activities_returns_data(client):
  response = client.get("/activities")
  assert response.status_code == 200
  data = response.json()
  assert "Chess Club" in data
  assert "participants" in data["Chess Club"]


def test_signup_adds_participant(client):
  activity = "Chess Club"
  email = "new_student@mergington.edu"

  response = client.post(f"/activities/{activity}/signup", params={"email": email})
  assert response.status_code == 200
  assert email in app_module.activities[activity]["participants"]


def test_signup_duplicate_rejected(client):
  activity = "Chess Club"
  existing_email = app_module.activities[activity]["participants"][0]

  response = client.post(f"/activities/{activity}/signup", params={"email": existing_email})
  assert response.status_code == 400
  assert "already" in response.json().get("detail", "").lower()


def test_unregister_removes_participant(client):
  activity = "Chess Club"
  email = app_module.activities[activity]["participants"][0]

  response = client.delete(f"/activities/{activity}/participants/{email}")
  assert response.status_code == 200
  assert email not in app_module.activities[activity]["participants"]
