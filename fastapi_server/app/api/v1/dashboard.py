"""Dashboard API — serves mock data for the ORIX Energy Reporting Agent demo."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Query

from app.mock_data import load_documents_data, load_financial_data, load_sfa_data

dashboard_router = APIRouter(prefix="/dashboard", tags=["dashboard"])

SEGMENTS = [
    "メガソーラー発電",
    "屋根借り太陽光",
    "風力発電（国内）",
    "風力発電（海外/Elawan）",
    "バイオマス発電",
    "地熱発電",
    "バイオガス発電",
    "蓄電所",
    "電力小売",
    "省エネサービス",
]


@dashboard_router.get("/kpis")
async def get_kpis() -> dict[str, Any]:
    """Return aggregated KPIs across all segments (latest month)."""
    data = load_financial_data()
    latest_month = max(r["month"] for r in data)
    latest = [r for r in data if r["month"] == latest_month]

    total_revenue = sum(r["revenue_million_yen"] for r in latest)
    total_profit = sum(r["operating_profit_million_yen"] for r in latest)
    total_capacity = sum(r["capacity_mw"] or 0 for r in latest)
    total_generation = sum(r["generation_mwh"] or 0 for r in latest)
    total_co2 = sum(r["co2_reduction_ton"] or 0 for r in latest)

    sfa = load_sfa_data()
    pipeline_count = len(sfa)
    pipeline_total = sum(d["amount_million_yen"] for d in sfa)
    pipeline_expected = sum(d["expected_amount_million_yen"] for d in sfa)

    return {
        "month": latest_month,
        "total_revenue_million_yen": total_revenue,
        "total_operating_profit_million_yen": total_profit,
        "total_capacity_mw": total_capacity,
        "total_generation_mwh": total_generation,
        "total_co2_reduction_ton": total_co2,
        "pipeline_count": pipeline_count,
        "pipeline_total_million_yen": pipeline_total,
        "pipeline_expected_million_yen": pipeline_expected,
        "segments": SEGMENTS,
    }


@dashboard_router.get("/financial")
async def get_financial(
    segment: str | None = Query(None, description="Filter by segment name"),
    period_from: str | None = Query(None, description="Start month (YYYY-MM)"),
    period_to: str | None = Query(None, description="End month (YYYY-MM)"),
) -> list[dict[str, Any]]:
    """Return monthly financial data (240 records)."""
    data = load_financial_data()
    if segment:
        data = [r for r in data if r["segment"] == segment]
    if period_from:
        data = [r for r in data if r["month"] >= period_from]
    if period_to:
        data = [r for r in data if r["month"] <= period_to]
    return data


@dashboard_router.get("/financial/{segment}")
async def get_financial_by_segment(segment: str) -> list[dict[str, Any]]:
    """Return financial data for a specific segment."""
    data = load_financial_data()
    return [r for r in data if r["segment"] == segment]


@dashboard_router.get("/sfa")
async def get_sfa(
    stage: str | None = Query(None, description="Filter by deal stage"),
    segment: str | None = Query(None, description="Filter by segment"),
) -> list[dict[str, Any]]:
    """Return SFA pipeline data (30 deals)."""
    data = load_sfa_data()
    if stage:
        data = [d for d in data if d["stage"] == stage]
    if segment:
        data = [d for d in data if d["segment"] == segment]
    return data


@dashboard_router.get("/sfa/summary")
async def get_sfa_summary() -> dict[str, Any]:
    """Return SFA pipeline summary grouped by stage."""
    data = load_sfa_data()
    stages: dict[str, dict[str, Any]] = {}
    for d in data:
        s = d["stage"]
        if s not in stages:
            stages[s] = {"count": 0, "total_million_yen": 0, "expected_million_yen": 0}
        stages[s]["count"] += 1
        stages[s]["total_million_yen"] += d["amount_million_yen"]
        stages[s]["expected_million_yen"] += d["expected_amount_million_yen"]
    return {
        "total_deals": len(data),
        "total_pipeline_million_yen": sum(d["amount_million_yen"] for d in data),
        "total_expected_million_yen": sum(
            d["expected_amount_million_yen"] for d in data
        ),
        "by_stage": stages,
    }


@dashboard_router.get("/documents")
async def get_documents(
    doc_type: str | None = Query(None, description="Filter by doc_type"),
    query: str | None = Query(None, description="Search in title/summary"),
) -> list[dict[str, Any]]:
    """Return internal documents list (20 docs)."""
    data = load_documents_data()
    if doc_type:
        data = [d for d in data if d["doc_type"] == doc_type]
    if query:
        q = query.lower()
        data = [d for d in data if q in d["title"].lower() or q in d["summary"].lower()]
    return data


# Generation segments (those with physical generation assets)
_GENERATION_SEGMENTS = {
    "メガソーラー発電",
    "屋根借り太陽光",
    "風力発電（国内）",
    "風力発電（海外/Elawan）",
    "バイオマス発電",
    "地熱発電",
    "バイオガス発電",
    "蓄電所",
}


@dashboard_router.get("/generation")
async def get_generation(
    segment: str | None = Query(None, description="Filter by generation segment"),
    period_from: str | None = Query(None, description="Start month (YYYY-MM)"),
    period_to: str | None = Query(None, description="End month (YYYY-MM)"),
) -> list[dict[str, Any]]:
    """Return generation performance data (capacity, output, utilization, CO2)."""
    data = load_financial_data()
    # Only include segments that have generation assets
    data = [r for r in data if r["segment"] in _GENERATION_SEGMENTS]
    if segment:
        data = [r for r in data if r["segment"] == segment]
    if period_from:
        data = [r for r in data if r["month"] >= period_from]
    if period_to:
        data = [r for r in data if r["month"] <= period_to]
    # Project only generation-related fields
    return [
        {
            "month": r["month"],
            "segment": r["segment"],
            "capacity_mw": r["capacity_mw"],
            "generation_mwh": r["generation_mwh"],
            "utilization_rate_pct": r["utilization_rate_pct"],
            "co2_reduction_ton": r["co2_reduction_ton"],
            "revenue_million_yen": r["revenue_million_yen"],
        }
        for r in data
    ]
