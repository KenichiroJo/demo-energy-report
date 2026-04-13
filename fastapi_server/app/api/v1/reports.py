"""Reports API — CRUD for persisted agent reports."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from app.reports import Report

reports_router = APIRouter(prefix="/reports", tags=["reports"])


# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------


class ReportCreate(BaseModel):
    title: str
    content: str
    report_type: str = "composite"
    summary: str | None = None
    metadata_json: dict[str, Any] | None = None
    chat_uuid: UUID | None = None


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@reports_router.get("")
async def list_reports(
    request: Request,
    report_type: str | None = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    deps = request.app.state.deps
    user = getattr(request.state, "user", None)
    user_uuid = user.uuid if user else None
    reports = await deps.report_repo.list_reports(
        user_uuid=user_uuid, report_type=report_type, limit=limit
    )
    return [
        {
            "uuid": str(r.uuid),
            "title": r.title,
            "report_type": r.report_type,
            "summary": r.summary,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in reports
    ]


@reports_router.get("/{report_id}")
async def get_report(report_id: UUID, request: Request) -> dict[str, Any]:
    deps = request.app.state.deps
    report = await deps.report_repo.get_report(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    # Also fetch any feedback for this report
    feedbacks = await deps.feedback_repo.get_report_feedback(report_id)
    return {
        "uuid": str(report.uuid),
        "title": report.title,
        "content": report.content,
        "report_type": report.report_type,
        "summary": report.summary,
        "metadata_json": report.metadata_json,
        "created_at": report.created_at.isoformat() if report.created_at else None,
        "feedbacks": [
            {
                "uuid": str(fb.uuid),
                "overall_rating": fb.overall_rating,
                "comment": fb.comment,
                "tags": fb.tags,
            }
            for fb in feedbacks
        ],
    }


@reports_router.post("")
async def create_report(body: ReportCreate, request: Request) -> dict[str, Any]:
    deps = request.app.state.deps
    user = getattr(request.state, "user", None)
    user_uuid = user.uuid if user else None

    report = Report(
        title=body.title,
        content=body.content,
        report_type=body.report_type,
        summary=body.summary,
        metadata_json=body.metadata_json,
        user_uuid=user_uuid,
        chat_uuid=body.chat_uuid,
    )
    created = await deps.report_repo.create_report(report)
    return {"uuid": str(created.uuid), "status": "created"}


@reports_router.delete("/{report_id}")
async def delete_report(report_id: UUID, request: Request) -> dict[str, str]:
    deps = request.app.state.deps
    deleted = await deps.report_repo.delete_report(report_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Report not found")
    return {"status": "deleted"}
