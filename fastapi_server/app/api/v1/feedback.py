"""Feedback API — message-level and report-level feedback endpoints."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from app.feedback import MessageFeedback, ReportFeedback

feedback_router = APIRouter(prefix="/feedback", tags=["feedback"])


# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------


class MessageFeedbackCreate(BaseModel):
    message_uuid: UUID
    rating: int  # 1 = thumbs-up, -1 = thumbs-down
    comment: str | None = None
    tags: list[str] | None = None


class MessageFeedbackUpdate(BaseModel):
    rating: int | None = None
    comment: str | None = None
    tags: list[str] | None = None


class ReportFeedbackCreate(BaseModel):
    report_uuid: UUID
    overall_rating: int  # 1-5
    accuracy_rating: int | None = None
    completeness_rating: int | None = None
    usefulness_rating: int | None = None
    comment: str | None = None
    tags: list[str] | None = None


class ReportFeedbackUpdate(BaseModel):
    overall_rating: int | None = None
    accuracy_rating: int | None = None
    completeness_rating: int | None = None
    usefulness_rating: int | None = None
    comment: str | None = None
    tags: list[str] | None = None


# ---------------------------------------------------------------------------
# Message feedback endpoints
# ---------------------------------------------------------------------------


@feedback_router.post("/message")
async def create_message_feedback(
    body: MessageFeedbackCreate, request: Request
) -> dict[str, Any]:
    deps = request.app.state.deps
    user = getattr(request.state, "user", None)
    user_uuid = user.uuid if user else None

    fb = MessageFeedback(
        message_uuid=body.message_uuid,
        user_uuid=user_uuid,
        rating=body.rating,
        comment=body.comment,
        tags=body.tags,
    )
    created = await deps.feedback_repo.create_message_feedback(fb)
    return {"uuid": str(created.uuid), "status": "created"}


@feedback_router.get("/message/{message_uuid}")
async def get_message_feedback(
    message_uuid: UUID, request: Request
) -> list[dict[str, Any]]:
    deps = request.app.state.deps
    feedbacks = await deps.feedback_repo.get_message_feedback(message_uuid)
    return [
        {
            "uuid": str(fb.uuid),
            "rating": fb.rating,
            "comment": fb.comment,
            "tags": fb.tags,
            "created_at": fb.created_at.isoformat() if fb.created_at else None,
        }
        for fb in feedbacks
    ]


@feedback_router.put("/message/{feedback_id}")
async def update_message_feedback(
    feedback_id: UUID, body: MessageFeedbackUpdate, request: Request
) -> dict[str, Any]:
    deps = request.app.state.deps
    updates = body.model_dump(exclude_unset=True)
    updated = await deps.feedback_repo.update_message_feedback(feedback_id, **updates)
    if not updated:
        raise HTTPException(status_code=404, detail="Feedback not found")
    return {"uuid": str(updated.uuid), "status": "updated"}


@feedback_router.delete("/message/{feedback_id}")
async def delete_message_feedback(
    feedback_id: UUID, request: Request
) -> dict[str, str]:
    deps = request.app.state.deps
    deleted = await deps.feedback_repo.delete_message_feedback(feedback_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Feedback not found")
    return {"status": "deleted"}


# ---------------------------------------------------------------------------
# Report feedback endpoints
# ---------------------------------------------------------------------------


@feedback_router.post("/report")
async def create_report_feedback(
    body: ReportFeedbackCreate, request: Request
) -> dict[str, Any]:
    deps = request.app.state.deps
    user = getattr(request.state, "user", None)
    user_uuid = user.uuid if user else None

    fb = ReportFeedback(
        report_uuid=body.report_uuid,
        user_uuid=user_uuid,
        overall_rating=body.overall_rating,
        accuracy_rating=body.accuracy_rating,
        completeness_rating=body.completeness_rating,
        usefulness_rating=body.usefulness_rating,
        comment=body.comment,
        tags=body.tags,
    )
    created = await deps.feedback_repo.create_report_feedback(fb)
    return {"uuid": str(created.uuid), "status": "created"}


@feedback_router.get("/report/{report_uuid}")
async def get_report_feedback(
    report_uuid: UUID, request: Request
) -> list[dict[str, Any]]:
    deps = request.app.state.deps
    feedbacks = await deps.feedback_repo.get_report_feedback(report_uuid)
    return [
        {
            "uuid": str(fb.uuid),
            "overall_rating": fb.overall_rating,
            "accuracy_rating": fb.accuracy_rating,
            "completeness_rating": fb.completeness_rating,
            "usefulness_rating": fb.usefulness_rating,
            "comment": fb.comment,
            "tags": fb.tags,
            "created_at": fb.created_at.isoformat() if fb.created_at else None,
        }
        for fb in feedbacks
    ]


@feedback_router.put("/report/{feedback_id}")
async def update_report_feedback(
    feedback_id: UUID, body: ReportFeedbackUpdate, request: Request
) -> dict[str, Any]:
    deps = request.app.state.deps
    updates = body.model_dump(exclude_unset=True)
    updated = await deps.feedback_repo.update_report_feedback(feedback_id, **updates)
    if not updated:
        raise HTTPException(status_code=404, detail="Feedback not found")
    return {"uuid": str(updated.uuid), "status": "updated"}


# ---------------------------------------------------------------------------
# Feedback summary (also used by agent tool)
# ---------------------------------------------------------------------------


@feedback_router.get("/summary")
async def get_feedback_summary(request: Request) -> dict[str, Any]:
    deps = request.app.state.deps
    return await deps.feedback_repo.get_feedback_summary()


@feedback_router.get("/summary/tags")
async def get_feedback_tags(request: Request) -> list[list[Any]]:
    deps = request.app.state.deps
    summary = await deps.feedback_repo.get_feedback_summary()
    return summary.get("top_tags", [])
