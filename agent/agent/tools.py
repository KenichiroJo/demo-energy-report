"""Environment & Energy reporting tools for the LangGraph agent.

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
        metric: 特定の指標名（売上高_百万円, 営業利益_百万円, 発電量_MWh 等）。省略で全指標。

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
        filtered = [r for r in filtered if segment in r.get("セグメント", "")]
    if year_month:
        filtered = [r for r in filtered if r.get("年月") == year_month]

    if metric:
        results = []
        for r in filtered:
            entry = {"セグメント": r["セグメント"], "年月": r["年月"]}
            if metric in r:
                entry[metric] = r[metric]
            results.append(entry)
        filtered = results

    # Summarise if the result set is large
    if len(filtered) > 30:
        segments = {}
        for r in filtered:
            seg = r.get("セグメント", "不明")
            if seg not in segments:
                segments[seg] = {
                    "件数": 0,
                    "売上高合計_百万円": 0,
                    "営業利益合計_百万円": 0,
                }
            segments[seg]["件数"] += 1
            segments[seg]["売上高合計_百万円"] += r.get("売上高_百万円", 0)
            segments[seg]["営業利益合計_百万円"] += r.get("営業利益_百万円", 0)
        return json.dumps(
            {"集計": True, "レコード数": len(filtered), "セグメント別": segments},
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
        filtered = [d for d in filtered if segment in d.get("セグメント", "")]
    if stage:
        filtered = [d for d in filtered if d.get("ステージ") == stage]
    if min_amount is not None:
        filtered = [d for d in filtered if d.get("案件金額_百万円", 0) >= min_amount]

    total_amount = sum(d.get("案件金額_百万円", 0) for d in filtered)
    total_expected = sum(d.get("期待金額_百万円", 0) for d in filtered)
    stage_summary = {}
    for d in filtered:
        s = d.get("ステージ", "不明")
        if s not in stage_summary:
            stage_summary[s] = {"件数": 0, "案件金額合計": 0, "期待金額合計": 0}
        stage_summary[s]["件数"] += 1
        stage_summary[s]["案件金額合計"] += d.get("案件金額_百万円", 0)
        stage_summary[s]["期待金額合計"] += d.get("期待金額_百万円", 0)

    return json.dumps(
        {
            "案件一覧": filtered,
            "サマリー": {
                "案件数": len(filtered),
                "案件金額合計_百万円": total_amount,
                "期待金額合計_百万円": total_expected,
                "ステージ別": stage_summary,
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
        filtered = [d for d in filtered if doc_type in d.get("文書種別", "")]
    if department:
        filtered = [d for d in filtered if department in d.get("所属部署", "")]
    if query:
        q_lower = query.lower()
        filtered = [
            d
            for d in filtered
            if q_lower in d.get("タイトル", "").lower()
            or q_lower in d.get("概要", "").lower()
            or any(q_lower in t.lower() for t in d.get("タグ", []))
        ]

    return json.dumps(
        {"文書一覧": filtered, "件数": len(filtered)},
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

    gen_data = [r for r in data if r.get("発電量_MWh") is not None]

    if segment:
        gen_data = [r for r in gen_data if segment in r.get("セグメント", "")]

    if period:
        if period == "latest":
            months = sorted(set(r["年月"] for r in gen_data))
            last_3 = months[-3:] if len(months) >= 3 else months
            gen_data = [r for r in gen_data if r["年月"] in last_3]
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
                if f"{year}-{start_m}" <= r["年月"] <= f"{year}-{end_m}"
            ]
        else:
            gen_data = [r for r in gen_data if r["年月"] == period]

    segments_summary = {}
    for r in gen_data:
        seg = r["セグメント"]
        if seg not in segments_summary:
            segments_summary[seg] = {
                "月数": 0,
                "発電量合計_MWh": 0,
                "設備利用率一覧": [],
                "設備容量_MW": 0,
            }
        segments_summary[seg]["月数"] += 1
        segments_summary[seg]["発電量合計_MWh"] += r.get("発電量_MWh", 0)
        if r.get("設備利用率_pct") is not None:
            segments_summary[seg]["設備利用率一覧"].append(r["設備利用率_pct"])
        segments_summary[seg]["設備容量_MW"] = max(
            segments_summary[seg]["設備容量_MW"], r.get("設備容量_MW", 0)
        )

    for seg_info in segments_summary.values():
        rates = seg_info.pop("設備利用率一覧")
        seg_info["平均設備利用率_pct"] = (
            round(sum(rates) / len(rates), 1) if rates else None
        )

    return json.dumps(
        {"発電実績分析": segments_summary, "レコード数": len(gen_data)},
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
