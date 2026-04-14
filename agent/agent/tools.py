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
_KPI: list[dict] | None = None
_ESG: list[dict] | None = None
_PROJECTS: list[dict] | None = None


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


def _kpi() -> list[dict]:
    global _KPI
    if _KPI is None:
        _KPI = _load_json("kpi_targets.json")
    return _KPI


def _esg() -> list[dict]:
    global _ESG
    if _ESG is None:
        _ESG = _load_json("esg.json")
    return _ESG


def _projects() -> list[dict]:
    global _PROJECTS
    if _PROJECTS is None:
        _PROJECTS = _load_json("projects.json")
    return _PROJECTS


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
                    "EBITDA合計_百万円": 0,
                    "予算_売上高合計_百万円": 0,
                    "予算_営業利益合計_百万円": 0,
                }
            segments[seg]["件数"] += 1
            segments[seg]["売上高合計_百万円"] += r.get("売上高_百万円", 0)
            segments[seg]["営業利益合計_百万円"] += r.get("営業利益_百万円", 0)
            segments[seg]["EBITDA合計_百万円"] += r.get("EBITDA_百万円", 0) or 0
            segments[seg]["予算_売上高合計_百万円"] += r.get("予算_売上高_百万円", 0) or 0
            segments[seg]["予算_営業利益合計_百万円"] += r.get("予算_営業利益_百万円", 0) or 0
        # Add budget achievement ratio
        for seg_info in segments.values():
            bud_rev = seg_info["予算_売上高合計_百万円"]
            seg_info["売上予算達成率_pct"] = (
                round(seg_info["売上高合計_百万円"] / bud_rev * 100, 1) if bud_rev else None
            )
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
        stage: ステージでフィルタ（リード, 提案, 交渉, 内定, 受注, 失注）。
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

    # Loss analysis
    lost_deals = [d for d in filtered if d.get("ステージ") == "失注"]
    loss_reasons = {}
    for d in lost_deals:
        reason = d.get("失注理由", "不明")
        if reason:
            loss_reasons[reason] = loss_reasons.get(reason, 0) + 1

    # Competitor analysis
    competitors = {}
    for d in filtered:
        comp = d.get("競合", "")
        if comp:
            competitors[comp] = competitors.get(comp, 0) + 1

    return json.dumps(
        {
            "案件一覧": filtered,
            "サマリー": {
                "案件数": len(filtered),
                "案件金額合計_百万円": total_amount,
                "期待金額合計_百万円": total_expected,
                "ステージ別": stage_summary,
                "失注理由分析": loss_reasons if loss_reasons else None,
                "競合出現頻度": competitors if competitors else None,
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
        query: 検索キーワード（タイトル、タグ、要約、関連セグメントに対して検索）。
        doc_type: 文書種別でフィルタ（事業計画, 月次報告, 議事録, 分析レポート, ESG報告, 技術評価, 規程 等）。
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
            or q_lower in d.get("関連セグメント", "").lower()
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


# ============================================================================
# Tool 6: KPI目標達成分析ツール
# ============================================================================
@tool
def analyze_kpi_performance(
    category: Optional[str] = None,
    fiscal_year: Optional[str] = None,
) -> str:
    """中期経営計画のKPI目標に対する達成状況を分析します。
    財務・事業・ESG・人材カテゴリのKPIを確認できます。

    Args:
        category: KPIカテゴリでフィルタ（財務, 事業, ESG, 人材）。省略で全カテゴリ。
        fiscal_year: 年度指定（例: "FY2024"）。省略で全年度を表示。

    Returns:
        JSON形式のKPI達成状況。
    """
    data = _kpi()
    if not data:
        return json.dumps(
            {"error": "KPIデータが読み込めませんでした"}, ensure_ascii=False
        )

    filtered = data
    if category:
        filtered = [d for d in filtered if d.get("カテゴリ") == category]

    results = []
    for kpi in filtered:
        entry = dict(kpi)
        # Add achievement analysis if fiscal_year specified
        if fiscal_year:
            actual_key = f"{fiscal_year}実績"
            target_key = f"{fiscal_year}目標"
            actual = kpi.get(actual_key)
            target = kpi.get(target_key)
            if actual is not None and target is not None and target != 0:
                entry["達成率_pct"] = round(actual / target * 100, 1)
                entry["差分"] = round(actual - target, 2)
        results.append(entry)

    return json.dumps(
        {"KPI一覧": results, "件数": len(results)},
        ensure_ascii=False,
    )


# ============================================================================
# Tool 7: ESG指標分析ツール
# ============================================================================
@tool
def analyze_esg_metrics(
    year_month: Optional[str] = None,
    metric: Optional[str] = None,
) -> str:
    """ESG（環境・社会・ガバナンス）関連指標の月次データを分析します。
    CO2削減量、再エネ供給量、カーボンクレジット、Scope排出量等を確認できます。

    Args:
        year_month: 年月でフィルタ（例: "2025-01"）。省略で全期間。
        metric: 特定のESG指標名で絞り込み（CO2削減量_t, 再エネ供給量_MWh 等）。

    Returns:
        JSON形式のESGデータとトレンド。
    """
    data = _esg()
    if not data:
        return json.dumps(
            {"error": "ESGデータが読み込めませんでした"}, ensure_ascii=False
        )

    filtered = data
    if year_month:
        filtered = [r for r in filtered if r.get("年月") == year_month]

    if metric:
        results = [{"年月": r["年月"], metric: r.get(metric)} for r in filtered]
        return json.dumps({"ESGデータ": results, "件数": len(results)}, ensure_ascii=False)

    # Provide cumulative/average summary if showing all data
    if len(filtered) > 6:
        totals = {
            "CO2削減量合計_t": sum(r.get("CO2削減量_t", 0) for r in filtered),
            "再エネ供給量合計_MWh": sum(r.get("再エネ供給量_MWh", 0) for r in filtered),
            "カーボンクレジット販売合計_百万円": sum(r.get("カーボンクレジット販売_百万円", 0) for r in filtered),
            "Scope1排出量合計_tCO2": sum(r.get("Scope1排出量_tCO2", 0) for r in filtered),
            "Scope2排出量合計_tCO2": sum(r.get("Scope2排出量_tCO2", 0) for r in filtered),
            "労災件数合計": sum(r.get("労災件数", 0) for r in filtered),
            "ヒヤリハット報告合計": sum(r.get("ヒヤリハット報告件数", 0) for r in filtered),
            "最新RE100供給企業数": max(r.get("RE100供給企業数", 0) for r in filtered),
        }
        return json.dumps(
            {"集計": True, "期間レコード数": len(filtered), "累計": totals, "月次データ": filtered},
            ensure_ascii=False,
        )

    return json.dumps({"ESGデータ": filtered, "件数": len(filtered)}, ensure_ascii=False)


# ============================================================================
# Tool 8: プロジェクト進捗分析ツール
# ============================================================================
@tool
def analyze_project_milestones(
    project_name: Optional[str] = None,
    segment: Optional[str] = None,
    status: Optional[str] = None,
) -> str:
    """主要プロジェクトのマイルストーン進捗を分析します。
    洋上風力、蓄電所、海外案件等の大型プロジェクトの状況を確認できます。

    Args:
        project_name: プロジェクト名で検索（部分一致）。
        segment: セグメント名でフィルタ。
        status: プロジェクトステータスでフィルタ（開発中, 建設中, 設計中, 調査中, FID承認済）。

    Returns:
        JSON形式のプロジェクト進捗データ。
    """
    data = _projects()
    if not data:
        return json.dumps(
            {"error": "プロジェクトデータが読み込めませんでした"}, ensure_ascii=False
        )

    filtered = data
    if project_name:
        filtered = [p for p in filtered if project_name in p.get("プロジェクト名", "")]
    if segment:
        filtered = [p for p in filtered if segment in p.get("セグメント", "")]
    if status:
        filtered = [p for p in filtered if p.get("ステータス") == status]

    # Add progress summary per project
    results = []
    for p in filtered:
        milestones = p.get("マイルストーン", [])
        total = len(milestones)
        completed = sum(1 for m in milestones if m.get("状態") == "完了")
        in_progress = sum(1 for m in milestones if m.get("状態") == "進行中")
        delayed = sum(
            1 for m in milestones
            if m.get("状態") == "完了" and m.get("実績日", "") > m.get("計画日", "")
        )
        entry = dict(p)
        entry["進捗サマリー"] = {
            "完了": completed,
            "進行中": in_progress,
            "未着手": total - completed - in_progress,
            "遅延あり": delayed,
            "進捗率_pct": round(completed / total * 100, 1) if total else 0,
        }
        results.append(entry)

    total_investment = sum(p.get("総投資額_億円", 0) for p in filtered)

    return json.dumps(
        {
            "プロジェクト一覧": results,
            "件数": len(results),
            "総投資額合計_億円": total_investment,
        },
        ensure_ascii=False,
    )


# ---------------------------------------------------------------------------
# Convenience: list of all tools for easy import
# ---------------------------------------------------------------------------
ALL_TOOLS = [
    analyze_financial_data,
    analyze_sfa_pipeline,
    search_documents,
    analyze_generation_data,
    get_user_feedback_context,
    analyze_kpi_performance,
    analyze_esg_metrics,
    analyze_project_milestones,
]
