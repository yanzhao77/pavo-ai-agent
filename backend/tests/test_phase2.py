"""Phase 2+3: Task status, versions, feedback endpoints."""
import pytest
import uuid
from unittest.mock import AsyncMock, MagicMock
from fastapi.testclient import TestClient
from app.main import app
from app.db.database import get_session
from app.models.project import Project, ProjectStatus, VersionHistory, Feedback

VALID_UUID = str(uuid.uuid4())


def make_session(project=None, versions=None, feedbacks=None, version=None):
    """Create a mock DB session for testing new endpoints."""
    session = AsyncMock()
    
    # Main result for scalar_one_or_none queries
    result_main = MagicMock()
    result_main.scalar_one_or_none.return_value = project
    session.execute.return_value = result_main
    
    # VersionHistory queries need special handling
    # For the first execute call (project query), use project
    # For version queries, we'll override
    
    # Handle scalars().all() results
    scalar_mock = MagicMock()
    scalar_mock.all.return_value = versions or []
    
    # For version count
    ver_scalar = MagicMock()
    ver_scalar.all.return_value = versions or []
    
    # We'll use side_effect for multiple execute calls
    async def execute_side_effect(*args, **kw):
        q = str(args[0]) if args else ""
        if "version_history" in q.lower():
            ver_result = MagicMock()
            ver_result.scalar_one_or_none.return_value = version
            return ver_result
        elif "VersionHistory" in q:
            list_result = MagicMock()
            list_result.scalars.return_value = ver_scalar
            return list_result
        elif "Feedback" in q:
            list_result = MagicMock()
            list_result.scalars.return_value = scalar_mock
            return list_result
        return result_main
    
    session.execute.side_effect = execute_side_effect
    session.commit = AsyncMock()
    session.add = MagicMock()
    session.refresh = AsyncMock()
    return session


@pytest.fixture(autouse=True)
def clear_overrides():
    app.dependency_overrides.clear()
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def client():
    return TestClient(app)


class TestTaskStatusEndpoint:
    """P2.3: GET /api/projects/{id}/tasks"""

    def test_task_status(self, client):
        p = Project(id=uuid.UUID(VALID_UUID), input_raw="test", user_id="u",
                    status=ProjectStatus.COMPLETED, task_ids=["task-1", "task-2"],
                    videos=[{"shot_number": 1}])
        session = make_session(project=p)
        app.dependency_overrides[get_session] = lambda: session
        resp = client.get(f"/api/projects/{VALID_UUID}/tasks")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["task_ids"]) == 2
        assert data["video_count"] == 1

    def test_task_status_not_found(self, client):
        session = make_session()
        app.dependency_overrides[get_session] = lambda: session
        resp = client.get(f"/api/projects/{VALID_UUID}/tasks")
        assert resp.status_code == 404


class TestVersionsEndpoints:
    """S10: Version history endpoints."""

    def test_create_version(self, client):
        p = Project(id=uuid.UUID(VALID_UUID), input_raw="test", user_id="u",
                    status=ProjectStatus.COMPLETED)
        session = make_session(project=p)
        app.dependency_overrides[get_session] = lambda: session
        resp = client.post(f"/api/projects/{VALID_UUID}/versions")
        assert resp.status_code == 200
        data = resp.json()
        assert "version_id" in data

    def test_list_versions(self, client):
        p = Project(id=uuid.UUID(VALID_UUID), input_raw="test", user_id="u",
                    status=ProjectStatus.COMPLETED)
        v = VersionHistory(id=uuid.uuid4(), project_id=uuid.UUID(VALID_UUID),
                          version_number=1, snapshot={}, description="v1")
        session = make_session(project=p, versions=[v])
        app.dependency_overrides[get_session] = lambda: session
        resp = client.get(f"/api/projects/{VALID_UUID}/versions")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)

    def test_restore_version_not_found(self, client):
        p = Project(id=uuid.UUID(VALID_UUID), input_raw="test", user_id="u",
                    status=ProjectStatus.COMPLETED)
        session = make_session(project=p, version=None)
        app.dependency_overrides[get_session] = lambda: session
        resp = client.post(f"/api/projects/{VALID_UUID}/versions/{VALID_UUID}/restore")
        assert resp.status_code == 404


class TestFeedbackEndpoints:
    """S14: Feedback endpoint."""

    def test_submit_feedback(self, client):
        p = Project(id=uuid.UUID(VALID_UUID), input_raw="test", user_id="u",
                    status=ProjectStatus.COMPLETED)
        session = make_session(project=p)
        app.dependency_overrides[get_session] = lambda: session
        resp = client.post(f"/api/projects/{VALID_UUID}/feedback", json={
            "rating": "up", "comment": "Great!", "user_id": "u"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "submitted"

    def test_submit_feedback_no_project(self, client):
        session = make_session()
        app.dependency_overrides[get_session] = lambda: session
        # Feedback POST doesn't check project existence directly
        resp = client.post(f"/api/projects/{VALID_UUID}/feedback", json={
            "rating": "down", "comment": "Needs work"
        })
        assert resp.status_code == 200

    def test_video_details(self, client):
        p = Project(id=uuid.UUID(VALID_UUID), input_raw="test", user_id="u",
                    status=ProjectStatus.COMPLETED,
                    videos=[{"shot_number": 1, "result": {"url": "http://example.com/v.mp4"}}])
        session = make_session(project=p)
        app.dependency_overrides[get_session] = lambda: session
        resp = client.get(f"/api/projects/{VALID_UUID}/videos")
        assert resp.status_code == 200

    def test_video_details_not_found(self, client):
        session = make_session()
        app.dependency_overrides[get_session] = lambda: session
        resp = client.get(f"/api/projects/{VALID_UUID}/videos")
        assert resp.status_code == 404


class TestDeleteEndpoint:
    """P1.1: DELETE project endpoint."""

    def test_delete_not_found(self, client):
        session = make_session()
        app.dependency_overrides[get_session] = lambda: session
        resp = client.delete(f"/api/projects/{VALID_UUID}")
        assert resp.status_code == 404

    def test_delete_success(self, client):
        from app.models.project import ProjectStatus
        p = Project(id=uuid.UUID(VALID_UUID), input_raw="test", user_id="u",
                    status=ProjectStatus.COMPLETED)
        session = make_session(project=p)
        app.dependency_overrides[get_session] = lambda: session
        resp = client.delete(f"/api/projects/{VALID_UUID}")
        assert resp.status_code == 200
        assert resp.json()["status"] == "deleted"
