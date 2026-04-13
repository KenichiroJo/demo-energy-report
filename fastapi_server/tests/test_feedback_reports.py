"""Tests for the Feedback and Reports API endpoints.

These tests use a real in-memory database to validate the full flow.
"""

import uuid as uuidpkg

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
async def client(make_authenticated_client):
    """Create an authenticated test client with a real in-memory DB."""
    return await make_authenticated_client()


class TestFeedbackMessageAPI:
    @pytest.mark.asyncio
    async def test_get_feedback_summary(self, client: TestClient) -> None:
        response = client.get("/api/v1/feedback/summary")
        assert response.status_code == 200
        data = response.json()
        assert "message_feedback_count" in data
        assert "report_feedback_count" in data

    @pytest.mark.asyncio
    async def test_get_feedback_tags(self, client: TestClient) -> None:
        response = client.get("/api/v1/feedback/summary/tags")
        assert response.status_code == 200
        data = response.json()
        # Returns a list of [tag, count] pairs (empty when no feedback exists)
        assert isinstance(data, list)


class TestReportsAPI:
    @pytest.mark.asyncio
    async def test_create_and_list_report(self, client: TestClient) -> None:
        # Create
        create_resp = client.post(
            "/api/v1/reports",
            json={
                "title": "テスト四半期レポート",
                "content": "# Q1レポート\n\n売上高: 10,000百万円",
                "report_type": "composite",
                "summary": "テストサマリー",
            },
        )
        assert create_resp.status_code == 200
        created = create_resp.json()
        assert "uuid" in created
        report_uuid = created["uuid"]

        # List
        list_resp = client.get("/api/v1/reports")
        assert list_resp.status_code == 200
        reports = list_resp.json()
        assert any(r["uuid"] == report_uuid for r in reports)

        # Get detail
        detail_resp = client.get(f"/api/v1/reports/{report_uuid}")
        assert detail_resp.status_code == 200
        detail = detail_resp.json()
        assert detail["title"] == "テスト四半期レポート"
        assert detail["content"] == "# Q1レポート\n\n売上高: 10,000百万円"
        assert detail["report_type"] == "composite"

        # Delete
        del_resp = client.delete(f"/api/v1/reports/{report_uuid}")
        assert del_resp.status_code == 200

        # Verify deleted
        get_resp = client.get(f"/api/v1/reports/{report_uuid}")
        assert get_resp.status_code == 404

    @pytest.mark.asyncio
    async def test_get_nonexistent_report(self, client: TestClient) -> None:
        response = client.get(f"/api/v1/reports/{uuidpkg.uuid4()}")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_list_reports_with_type_filter(self, client: TestClient) -> None:
        # Create two reports with different types
        client.post(
            "/api/v1/reports",
            json={
                "title": "財務レポート",
                "content": "...",
                "report_type": "financial",
            },
        )
        client.post(
            "/api/v1/reports",
            json={"title": "SFAレポート", "content": "...", "report_type": "sfa"},
        )

        # Filter by type
        resp = client.get("/api/v1/reports", params={"report_type": "financial"})
        assert resp.status_code == 200
        reports = resp.json()
        assert all(r["report_type"] == "financial" for r in reports)
