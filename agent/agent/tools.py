"""ORIX Environment & Energy reporting tools for the LangGraph agent.

These tools operate on mock data bundled in fastapi_server/app/mock_data/.
In production, they would query Databricks / SharePoint via appropriate connectors.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from langchain_core.tools import tool

# ---------------------------------------------------------------------------
# Data loading – resolve relative to this file so it works in any cwd.
# The mock JSON lives under fastapi_server/app/mock_data/ (sibling package).
# At runtime the agent wheel has them installed, but for local dev we also
# support a copy next to this module.
# ---------------------------------------------------------------------------
_THIS_DIR = Path(__file__).resolve().parent
_MOCK_DIR_CANDIDATES = [
    _THIS_DIR / "mock_data",
    _THIS_DIR.parents[2] / "fastapi_server" / "app" / "mock_data",
]
_MOCK_DIR: Path | None = None
for _c in _MOCK_DIR_CANDIDATES:
    if _c.is_dir():
        _MOCK_DIR = _c
        break


def _load_json(name: str) -> list[dict]:
    if _MOCK_DIR is None:
        return []
    with open(_MOCK_DIR / name, encoding="utf-8") as f:
        return json.load(f)


_FINANCIAL: list[dict] | None = None
_SFA: list[dict] | None = None
_DOCUMENTS: list[dict] | None = None


def _financial() -> list[dict]:
    global _FINANCIAL
    if _FINANCIAL is None:
        _FINANCIAL = _load_json("financial.json")
    return _FINANCIAL


def _sfa() -> list[dict]:
    global _SFA
    if _SFA is None:
        _SFA = _load_json("sfa.json")
    return _SFA


def _documents() -> list[dict]:
    global _DOCUMENTS
    if _DOCUMENTS is None:
        _DOCUMENTS = _load_json("documents.json")
    return _DOCUMENTS


# ============================================================================
# Tool 1: 財務分析ツール
# ============================================================================
@tool
def analyze_financial_data(
    segment: Optional[str] = None,
    year_month: Optional[str] = None,
    metric: Optional[str] = None,
) -> str:
    """環境エネルギー本部の財務データを分析します。
    セグメント別・月別の売上、利益、発電量等を取得できます。

    Args:
        segment: セグメント名でフィルタ（例: メガソーラー発電, 風力発電（国内））。省略で全セグメント。
        year_month: 年月でフィルタ（例: 2025-01）。省略で全期間。
        metric: 特定の指標名（revenue, operating_profit, generation_mwh 等）。省略で全指標。

    Returns:
        JSON形式の財務データ。
    """
    data = _financial()
    if not data:
        return json.dumps(
            {"error": "財務データが読み込めませんでした"}, ensure_ascii=False
        )

    filtered = data
    if segment:
        filtered = [r for r in filtered if segment in r.get("segment", "")]
    if year_month:
        filtered = [r for r in filtered if r.get("month") == year_month]

    if metric:
        results = []
        for r in filtered:
            entry = {"segment": r["segment"], "year_month": r["month"]}
            if metric in r:
                entry[metric] = r[metric]
            results.append(entry)
        filtered = results

    # Summarise if the result set is large
    if len(filtered) > 30:
        # Return aggregated summary instead
        segments = {}
        for r in filtered:
            seg = r.get("segment", "unknown")
            if seg not in segments:
                segments[seg] = {
                    "count": 0,
                    "total_revenue": 0,
                    "total_operating_profit": 0,
                }
            segments[seg]["count"] += 1
            segments[seg]["total_revenue"] += r.get("revenue_million_yen", 0)
            segments[seg]["total_operating_profit"] += r.get(
                "operating_profit_million_yen", 0
            )
        return json.dumps(
            {"summary": True, "record_count": len(filtered), "by_segment": segments},
            ensure_ascii=False,
        )

    return json.dumps(filtered, ensure_ascii=False)


# ============================================================================
# Tool 2: SFA パイプライン分析ツール
# ============================================================================
@tool
def analyze_sfa_pipeline(
    segment: Optional[str] = None,
    stage: Optional[str] = None,
    min_amount: Optional[float] = None,
) -> str:
    """SFA（営業支援システム）のパイプラインデータを分析します。
    案件のステージ、金額、受注確度等を取得できます。

    Args:
        segment: セグメント名でフィルタ。
        stage: ステージでフィルタ（リード, 提案, 交渉, 内定, 受注）。
        min_amount: 最低金額（百万円）でフィルタ。

    Returns:
        JSON形式のSFAパイプラインデータ。
    """
    data = _sfa()
    if not data:
        return json.dumps(
            {"error": "SFAデータが読み込めませんでした"}, ensure_ascii=False
        )

    filtered = data
    if segment:
        filtered = [d for d in filtered if segment in d.get("segment", "")]
    if stage:
        filtered = [d for d in filtered if d.get("stage") == stage]
    if min_amount is not None:
        filtered = [d for d in filtered if d.get("amount_million_yen", 0) >= min_amount]

    # Also compute a quick summary
    total_amount = sum(d.get("amount_million_yen", 0) for d in filtered)
    total_expected = sum(d.get("expected_amount_million_yen", 0) for d in filtered)
    stage_summary = {}
    for d in filtered:
        s = d.get("stage", "不明")
        if s not in stage_summary:
            stage_summary[s] = {"count": 0, "amount": 0, "expected": 0}
        stage_summary[s]["count"] += 1
        stage_summary[s]["amount"] += d.get("amount_million_yen", 0)
        stage_summary[s]["expected"] += d.get("expected_amount_million_yen", 0)

    return json.dumps(
        {
            "deals": filtered,
            "summary": {
                "total_deals": len(filtered),
                "total_amount_million_yen": total_amount,
                "total_expected_amount_million_yen": total_expected,
                "by_stage": stage_summary,
            },
        },
        ensure_ascii=False,
    )


# ============================================================================
# Tool 3: 文書検索・要約ツール
# ============================================================================
@tool
def search_documents(
    query: Optional[str] = None,
    doc_type: Optional[str] = None,
    department: Optional[str] = None,
) -> str:
    """社内文書（事業計画書、議事録、報告書等）を検索・要約します。

    Args:
        query: 検索キーワード（タイトル、タグ、要約に対して検索）。
        doc_type: 文書種別でフィルタ（事業計画書, 議事録, 報告書, 分析レポート 等）。
        department: 部署名でフィルタ。

    Returns:
        JSON形式の文書一覧と要約。
    """
    data = _documents()
    if not data:
        return json.dumps(
            {"error": "文書データが読み込めませんでした"}, ensure_ascii=False
        )

    filtered = data
    if doc_type:
        filtered = [d for d in filtered if doc_type in d.get("doc_type", "")]
    if department:
        filtered = [d for d in filtered if department in d.get("department", "")]
    if query:
        q_lower = query.lower()
        filtered = [
            d
            for d in filtered
            if q_lower in d.get("title", "").lower()
            or q_lower in d.get("summary", "").lower()
            or any(q_lower in t.lower() for t in d.get("tags", []))
        ]

    return json.dumps(
        {"documents": filtered, "total": len(filtered)},
        ensure_ascii=False,
    )


# ============================================================================
# Tool 4: 発電実績・予測ツール
# ============================================================================
@tool
def analyze_generation_data(
    segment: Optional[str] = None,
    period: Optional[str] = None,
) -> str:
    """発電実績（設備容量、発電量、稼働率）を分析し、トレンドを提示します。

    Args:
        segment: 発電セグメント名（メガソーラー発電, 風力発電（国内）等）。
        period: 期間指定（例: "2025-Q1", "2025-01"～"2025-03", "latest"）。"latest" は直近3ヶ月。

    Returns:
        JSON形式の発電データとトレンド分析。
    """
    data = _financial()  # generation info is embedded in financial data
    if not data:
        return json.dumps(
            {"error": "発電データが読み込めませんでした"}, ensure_ascii=False
        )

    # Filter to records that have generation data
    gen_data = [r for r in data if r.get("generation_mwh") is not None]

    if segment:
        gen_data = [r for r in gen_data if segment in r.get("segment", "")]

    if period:
        if period == "latest":
            # Get unique months and take last 3
            months = sorted(set(r["month"] for r in gen_data))
            last_3 = months[-3:] if len(months) >= 3 else months
            gen_data = [r for r in gen_data if r["month"] in last_3]
        elif "-Q" in period:
            year, q = period.split("-Q")
            q = int(q)
            month_ranges = {
                1: ("01", "03"),
                2: ("04", "06"),
                3: ("07", "09"),
                4: ("10", "12"),
            }
            start_m, end_m = month_ranges.get(q, ("01", "03"))
            gen_data = [
                r
                for r in gen_data
                if f"{year}-{start_m}" <= r["month"] <= f"{year}-{end_m}"
            ]
        else:
            gen_data = [r for r in gen_data if r["month"] == period]

    # Build summary
    segments_summary = {}
    for r in gen_data:
        seg = r["segment"]
        if seg not in segments_summary:
            segments_summary[seg] = {
                "months": [],
                "total_generation_mwh": 0,
                "avg_utilization_pct": [],
                "total_capacity_mw": 0,
            }
        segments_summary[seg]["months"].append(r["month"])
        segments_summary[seg]["total_generation_mwh"] += r.get("generation_mwh", 0)
        if r.get("utilization_rate_pct") is not None:
            segments_summary[seg]["avg_utilization_pct"].append(
                r["utilization_rate_pct"]
            )
        segments_summary[seg]["total_capacity_mw"] = max(
            segments_summary[seg]["total_capacity_mw"], r.get("capacity_mw", 0)
        )

    # Compute averages
    for seg_info in segments_summary.values():
        rates = seg_info.pop("avg_utilization_pct")
        seg_info["avg_utilization_pct"] = (
            round(sum(rates) / len(rates), 1) if rates else None
        )
        seg_info["month_count"] = len(seg_info.pop("months"))

    return json.dumps(
        {"generation_analysis": segments_summary, "record_count": len(gen_data)},
        ensure_ascii=False,
    )


# ============================================================================
# Tool 5: フィードバック取得ツール
# ============================================================================
@tool
def get_user_feedback_context() -> str:
    """過去のユーザーフィードバック（評価・コメント・タグ）を取得し、
    レポート品質改善に活用します。直近のフィードバック傾向を分析して返します。

    Returns:
        JSON形式のフィードバックサマリー。
    """
    # In demo mode, return a static representative summary.
    # In production, this would call the FastAPI feedback API.
    summary = {
        "message_feedback": {
            "total_count": 42,
            "avg_rating": 4.1,
            "recent_comments": [
                "セグメント別の比較がとても見やすい",
                "SFAデータの更新頻度をもう少し上げてほしい",
                "風力発電の稼働率トレンドが参考になった",
            ],
            "top_tags": ["有用", "正確", "改善希望:詳細度"],
        },
        "report_feedback": {
            "total_count": 15,
            "avg_overall_rating": 3.8,
            "avg_accuracy_rating": 4.2,
            "avg_completeness_rating": 3.5,
            "avg_usefulness_rating": 4.0,
            "improvement_suggestions": [
                "CO2削減量の前年比較を追加してほしい",
                "海外案件のリスク分析をもう少し深掘りしてほしい",
            ],
        },
    }
    return json.dumps(summary, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Convenience: list of all tools for easy import
# ---------------------------------------------------------------------------
ALL_TOOLS = [
    analyze_financial_data,
    analyze_sfa_pipeline,
    search_documents,
    analyze_generation_data,
    get_user_feedback_context,
]
