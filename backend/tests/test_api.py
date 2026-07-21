"""Phase 1 - P1.1: API endpoint tests."""
import pytest
import uuid
from unittest.mock import AsyncMock, MagicMock
from fastapi.testclient import TestClient
from app.main import app
from app.db.database import get_session
from app.models.project import Project, ProjectStatus


VALID_UUID = str(uuid.uuid4())


@pytest.fixture(autouse=True)
def clear_overrides():
    app.dependency_overrides.clear()
    yield
    app.dependency_overrides.clear()


def make_session_mock(project=None, projects=None):
    """Create a mock DB session."""
    session = AsyncMock()
    # Result from await session.execute(query) - sync methods
    result_mock = MagicMock()
    result_mock.scalar_one_or_none.return_value = project
   
    # .scalars() is sync, .all() is sync
    scalars_mock = MagicMock()
    scalars_mock.all.return_value = projects or []
    result_mock.scalars.return_value = scalars_mock
   
    # session.execute is async - returns result_mock when awaited
    session.execute = AsyncMock(return_value=result_mock)
    session.commit = AsyncMock()
    session.add = MagicMock()
    return session


@pytest.fixture
def client():
    return TestClient(app)


class TestHealthEndpoint:
    def test_health_ok(self, client):
        resp = client.get("/api/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"


class TestAuthEndpoints:
    def test_login_success(self, client):
        resp = client.post("/api/auth/login", json={"username": "testuser"})
        assert resp.status_code == 200
        data = resp.json()
        assert "token" in data
        assert data["user_id"] == "testuser"

    def test_login_empty(self, client):
        resp = client.post("/api/auth/login", json={"username": ""})
        assert resp.status_code == 400

    def test_login_normalize(self, client):
        resp = client.post("/api/auth/login", json={"username": "  A B  "})
        assert resp.status_code == 200
        assert resp.json()["user_id"] == "a_b"

    def test_auth_me_valid(self, client):
        r = client.post("/api/auth/login", json={"username": "x"})
        token = r.json()["token"]
        resp = client.get(f"/api/auth/me?token={token}")
        assert resp.status_code == 200

    def test_auth_me_invalid(self, client):
        resp = client.get("/api/auth/me?token=bad")
        assert resp.status_code == 401

    def test_auth_me_no_token(self, client):
        resp = client.get("/api/auth/me")
        assert resp.status_code == 401


class TestProjectEndpoints:
    def test_create_project(self, client):
        session = make_session_mock()
        app.dependency_overrides[get_session] = lambda: session
        resp = client.post("/api/projects", json={"input": "test story"})
        assert resp.status_code == 200
        assert "projectId" in resp.json()

    def test_get_project_not_found(self, client):
        session = make_session_mock()
        app.dependency_overrides[get_session] = lambda: session
        resp = client.get(f"/api/projects/{VALID_UUID}")
        assert resp.status_code == 404

    def test_get_project_found(self, client):
        p = Project(id=uuid.UUID(VALID_UUID), input_raw="test", user_id="u", status=ProjectStatus.COMPLETED)
        session = make_session_mock(project=p)
        app.dependency_overrides[get_session] = lambda: session
        resp = client.get(f"/api/projects/{VALID_UUID}")
        assert resp.status_code == 200
        assert "input" in resp.json()

    def test_list_projects(self, client):
        p = Project(id=uuid.UUID(VALID_UUID), input_raw="t", user_id="u", status=ProjectStatus.GENERATING)
        session = make_session_mock(projects=[p])
        app.dependency_overrides[get_session] = lambda: session
        resp = client.get("/api/projects?user_id=u")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_update_not_found(self, client):
        session = make_session_mock()
        app.dependency_overrides[get_session] = lambda: session
        resp = client.patch(f"/api/projects/{VALID_UUID}", json={"title": "New"})
        assert resp.status_code == 404

    def test_update_found(self, client):
        p = Project(id=uuid.UUID(VALID_UUID), input_raw="t", user_id="u", status=ProjectStatus.DRAFT)
        session = make_session_mock(project=p)
        app.dependency_overrides[get_session] = lambda: session
        resp = client.patch(f"/api/projects/{VALID_UUID}", json={"title": "New"})
        assert resp.status_code == 200


class TestSSEEndpoint:
    """P1.4: SSE stream endpoint tests."""

    def test_sse_project_not_found(self, client):
        session = make_session_mock()
        app.dependency_overrides[get_session] = lambda: session
        resp = client.get(f"/api/projects/{VALID_UUID}/stream")
        assert resp.status_code == 404

    def test_sse_completed_project(self, client):
        p = Project(id=uuid.UUID(VALID_UUID), input_raw="test", user_id="u",
                    status=ProjectStatus.COMPLETED, trace_log=[{
                        "agent": "test", "action": "done",
                        "status": "passed", "timestamp": "2026-01-01T00:00:00"
                    }])
        session = make_session_mock(project=p)
        session.refresh = AsyncMock()
        app.dependency_overrides[get_session] = lambda: session
        with client.stream("GET", f"/api/projects/{VALID_UUID}/stream") as resp:
            assert resp.status_code == 200
            resp.read()
            data = resp.text
            assert "complete" in data
