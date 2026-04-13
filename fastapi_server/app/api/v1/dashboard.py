"""Dashboard API — serves mock data for the Energy Reporting Agent demo."""

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
    latest_month = max(r["年月"] for r in data)
    latest = [r for r in data if r["年月"] == latest_month]

    total_revenue = sum(r["売上高_百万円"] for r in latest)
    total_profit = sum(r["営業利益_百万円"] for r in latest)
    total_capacity = sum(r["設備容量_MW"] or 0 for r in latest)
    total_generation = sum(r["発電量_MWh"] or 0 for r in latest)
    total_co2 = sum(r["CO2削減量_t"] or 0 for r in latest)

    sfa = load_sfa_data()
    pipeline_count = len(sfa)
    pipeline_total = sum(d["案件金額_百万円"] for d in sfa)
    pipeline_expected = sum(d["期待金額_百万円"] for d in sfa)

    return {
        "年月": latest_month,
        "売上高合計_百万円": total_revenue,
        "営業利益合計_百万円": total_profit,
        "設備容量合計_MW": total_capacity,
        "発電量合計_MWh": total_generation,
        "CO2削減量合計_t": total_co2,
        "パイプライン件数": pipeline_count,
        "パイプライン金額合計_百万円": pipeline_total,
        "パイプライン期待金額合計_百万円": pipeline_expected,
        "セグメント一覧": SEGMENTS,
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
        data = [r for r in data if r["セグメント"] == segment]
    if period_from:
        data = [r for r in data if r["年月"] >= period_from]
    if period_to:
        data = [r for r in data if r["年月"] <= period_to]
    return data


@dashboard_router.get("/financial/{segment}")
async def get_financial_by_segment(segment: str) -> list[dict[str, Any]]:
    """Return financial data for a specific segment."""
    data = load_financial_data()
    return [r for r in data if r["セグメント"] == segment]


@dashboard_router.get("/sfa")
async def get_sfa(
    stage: str | None = Query(None, description="Filter by deal stage"),
    segment: str | None = Query(None, description="Filter by segment"),
) -> list[dict[str, Any]]:
    """Return SFA pipeline data (30 deals)."""
    data = load_sfa_data()
    if stage:
        data = [d for d in data if d["ステージ"] == stage]
    if segment:
        data = [d for d in data if d["セグメント"] == segment]
    return data


@dashboard_router.get("/sfa/summary")
async def get_sfa_summary() -> dict[str, Any]:
    """Return SFA pipeline summary grouped by stage."""
    data = load_sfa_data()
    stages: dict[str, dict[str, Any]] = {}
    for d in data:
        s = d["ステージ"]
        if s not in stages:
            stages[s] = {"件数": 0, "案件金額合計_百万円": 0, "期待金額合計_百万円": 0}
        stages[s]["件数"] += 1
        stages[s]["案件金額合計_百万円"] += d["案件金額_百万円"]
        stages[s]["期待金額合計_百万円"] += d["期待金額_百万円"]
    return {
        "案件数": len(data),
        "パイプライン金額合計_百万円": sum(d["案件金額_百万円"] for d in data),
        "期待金額合計_百万円": sum(d["期待金額_百万円"] for d in data),
        "ステージ別": stages,
    }


@dashboard_router.get("/documents")
async def get_documents(
    doc_type: str | None = Query(None, description="Filter by doc_type"),
    query: str | None = Query(None, description="Search in title/summary"),
) -> list[dict[str, Any]]:
    """Return internal documents list (20 docs)."""
    data = load_documents_data()
    if doc_type:
        data = [d for d in data if d["文書種別"] == doc_type]
    if query:
        q = query.lower()
        data = [d for d in data if q in d["タイトル"].lower() or q in d["概要"].lower()]
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
    data = [r for r in data if r["セグメント"] in _GENERATION_SEGMENTS]
    if segment:
        data = [r for r in data if r["セグメント"] == segment]
    if period_from:
        data = [r for r in data if r["年月"] >= period_from]
    if period_to:
        data = [r for r in data if r["年月"] <= period_to]
    return [
        {
            "年月": r["年月"],
            "セグメント": r["セグメント"],
            "設備容量_MW": r["設備容量_MW"],
            "発電量_MWh": r["発電量_MWh"],
            "設備利用率_pct": r["設備利用率_pct"],
            "CO2削減量_t": r["CO2削減量_t"],
            "売上高_百万円": r["売上高_百万円"],
        }
        for r in data
    ]
