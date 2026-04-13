"""Tests for the Energy Reporting agent tools."""

import json

from agent.tools import (
    ALL_TOOLS,
    analyze_financial_data,
    analyze_generation_data,
    analyze_sfa_pipeline,
    get_user_feedback_context,
    search_documents,
)


class TestAnalyzeFinancialData:
    def test_returns_all_data_summarized(self) -> None:
        result = json.loads(analyze_financial_data.invoke({}))
        # 240 records > 30, so should return summary
        assert result["summary"] is True
        assert result["record_count"] == 240
        assert "by_segment" in result
        assert len(result["by_segment"]) == 10

    def test_filter_by_segment(self) -> None:
        result = json.loads(
            analyze_financial_data.invoke({"segment": "メガソーラー発電"})
        )
        # 24 records for one segment — under 30 threshold
        assert isinstance(result, list)
        assert len(result) == 24
        assert all(r["segment"] == "メガソーラー発電" for r in result)

    def test_filter_by_year_month(self) -> None:
        result = json.loads(analyze_financial_data.invoke({"year_month": "2025-01"}))
        assert isinstance(result, list)
        assert len(result) == 10  # one per segment
        assert all(r["month"] == "2025-01" for r in result)

    def test_filter_by_metric(self) -> None:
        result = json.loads(
            analyze_financial_data.invoke(
                {"segment": "メガソーラー発電", "metric": "revenue_million_yen"}
            )
        )
        assert isinstance(result, list)
        for r in result:
            assert "revenue_million_yen" in r
            assert "segment" in r
            assert "year_month" in r


class TestAnalyzeSfaPipeline:
    def test_returns_all_deals(self) -> None:
        result = json.loads(analyze_sfa_pipeline.invoke({}))
        assert "deals" in result
        assert "summary" in result
        assert result["summary"]["total_deals"] == 30

    def test_filter_by_stage(self) -> None:
        result = json.loads(analyze_sfa_pipeline.invoke({"stage": "交渉"}))
        for d in result["deals"]:
            assert d["stage"] == "交渉"

    def test_filter_by_min_amount(self) -> None:
        result = json.loads(analyze_sfa_pipeline.invoke({"min_amount": 10000}))
        for d in result["deals"]:
            assert d["amount_million_yen"] >= 10000


class TestSearchDocuments:
    def test_returns_all_documents(self) -> None:
        result = json.loads(search_documents.invoke({}))
        assert result["total"] == 20

    def test_search_by_query(self) -> None:
        result = json.loads(search_documents.invoke({"query": "風力"}))
        assert result["total"] > 0
        for d in result["documents"]:
            found = (
                "風力" in d.get("title", "")
                or "風力" in d.get("summary", "")
                or any("風力" in t for t in d.get("tags", []))
            )
            assert found

    def test_filter_by_doc_type(self) -> None:
        result = json.loads(search_documents.invoke({"doc_type": "報告書"}))
        for d in result["documents"]:
            assert "報告書" in d["doc_type"]


class TestAnalyzeGenerationData:
    def test_returns_all_generation(self) -> None:
        result = json.loads(analyze_generation_data.invoke({}))
        assert "generation_analysis" in result
        assert result["record_count"] > 0

    def test_filter_by_segment(self) -> None:
        result = json.loads(
            analyze_generation_data.invoke({"segment": "メガソーラー発電"})
        )
        assert "メガソーラー発電" in result["generation_analysis"]
        assert len(result["generation_analysis"]) == 1

    def test_latest_period(self) -> None:
        result = json.loads(analyze_generation_data.invoke({"period": "latest"}))
        assert result["record_count"] > 0
        # Should be limited to 3 months
        for seg_info in result["generation_analysis"].values():
            assert seg_info["month_count"] <= 3


class TestGetUserFeedbackContext:
    def test_returns_feedback_summary(self) -> None:
        result = json.loads(get_user_feedback_context.invoke({}))
        assert "message_feedback" in result
        assert "report_feedback" in result
        assert "avg_rating" in result["message_feedback"]
        assert "avg_overall_rating" in result["report_feedback"]


class TestToolsList:
    def test_all_tools_count(self) -> None:
        assert len(ALL_TOOLS) == 5

    def test_all_tools_have_names(self) -> None:
        for tool in ALL_TOOLS:
            assert tool.name
            assert tool.description
