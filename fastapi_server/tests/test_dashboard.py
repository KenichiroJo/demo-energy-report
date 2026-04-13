"""Tests for the Dashboard API endpoints."""

import pytest
from fastapi.testclient import TestClient


class TestDashboardAPI:
    @pytest.fixture
    def client(self, simple_client: TestClient) -> TestClient:
        return simple_client

    def test_get_kpis(self, client: TestClient) -> None:
        response = client.get("/api/v1/dashboard/kpis")
        assert response.status_code == 200
        data = response.json()
        assert "month" in data
        assert "total_revenue_million_yen" in data
        assert "total_operating_profit_million_yen" in data
        assert "total_capacity_mw" in data
        assert "total_generation_mwh" in data
        assert "total_co2_reduction_ton" in data
        assert "pipeline_count" in data
        assert "segments" in data
        assert len(data["segments"]) == 10

    def test_get_financial_all(self, client: TestClient) -> None:
        response = client.get("/api/v1/dashboard/financial")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 240  # 24 months × 10 segments

    def test_get_financial_by_segment_filter(self, client: TestClient) -> None:
        response = client.get(
            "/api/v1/dashboard/financial",
            params={"segment": "メガソーラー発電"},
        )
        assert response.status_code == 200
        data = response.json()
        assert all(r["segment"] == "メガソーラー発電" for r in data)
        assert len(data) == 24

    def test_get_financial_by_period(self, client: TestClient) -> None:
        response = client.get(
            "/api/v1/dashboard/financial",
            params={"period_from": "2025-01", "period_to": "2025-03"},
        )
        assert response.status_code == 200
        data = response.json()
        for r in data:
            assert "2025-01" <= r["month"] <= "2025-03"

    def test_get_financial_by_segment_path(self, client: TestClient) -> None:
        response = client.get("/api/v1/dashboard/financial/メガソーラー発電")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 24
        assert all(r["segment"] == "メガソーラー発電" for r in data)

    def test_get_sfa_all(self, client: TestClient) -> None:
        response = client.get("/api/v1/dashboard/sfa")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 30

    def test_get_sfa_by_stage(self, client: TestClient) -> None:
        response = client.get("/api/v1/dashboard/sfa", params={"stage": "交渉"})
        assert response.status_code == 200
        data = response.json()
        assert all(d["stage"] == "交渉" for d in data)

    def test_get_sfa_summary(self, client: TestClient) -> None:
        response = client.get("/api/v1/dashboard/sfa/summary")
        assert response.status_code == 200
        data = response.json()
        assert "total_deals" in data
        assert data["total_deals"] == 30
        assert "by_stage" in data

    def test_get_documents_all(self, client: TestClient) -> None:
        response = client.get("/api/v1/dashboard/documents")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 20

    def test_get_documents_search(self, client: TestClient) -> None:
        response = client.get("/api/v1/dashboard/documents", params={"query": "風力"})
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0
        for d in data:
            assert "風力" in d["title"].lower() or "風力" in d["summary"].lower()

    def test_get_generation_all(self, client: TestClient) -> None:
        response = client.get("/api/v1/dashboard/generation")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # 8 generation segments × 24 months = 192
        assert len(data) == 192
        # Verify projected fields
        for r in data:
            assert "month" in r
            assert "segment" in r
            assert "capacity_mw" in r
            assert "generation_mwh" in r
            assert "utilization_rate_pct" in r
            assert "co2_reduction_ton" in r
            # Should NOT include cost/profit fields (projected away)
            assert "cost_million_yen" not in r
            assert "operating_profit_million_yen" not in r

    def test_get_generation_by_segment(self, client: TestClient) -> None:
        response = client.get(
            "/api/v1/dashboard/generation",
            params={"segment": "風力発電（国内）"},
        )
        assert response.status_code == 200
        data = response.json()
        assert all(r["segment"] == "風力発電（国内）" for r in data)
        assert len(data) == 24
