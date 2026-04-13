import logging
import uuid as uuidpkg
from datetime import datetime, timezone
from typing import Any, Sequence

from sqlalchemy import JSON, Column, DateTime, ForeignKey
from sqlmodel import Field, SQLModel, UniqueConstraint, select

from app.db import DBCtx

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


class MessageFeedback(SQLModel, table=True):
    """Per-message feedback (thumbs up / down + optional comment & tags)."""

    __tablename__ = "message_feedback"
    __table_args__ = (
        UniqueConstraint("message_uuid", "user_uuid", name="uq_msg_fb_user"),
    )

    uuid: uuidpkg.UUID = Field(default_factory=uuidpkg.uuid4, primary_key=True)
    message_uuid: uuidpkg.UUID = Field(
        sa_column=Column(
            "message_uuid",
            ForeignKey("message.uuid", ondelete="CASCADE"),
            nullable=False,
            index=True,
        )
    )
    user_uuid: uuidpkg.UUID = Field(
        sa_column=Column(
            "user_uuid",
            ForeignKey("user.uuid", ondelete="CASCADE"),
            nullable=False,
            index=True,
        )
    )
    rating: int = Field(default=0)  # 1 = thumbs-up, -1 = thumbs-down
    comment: str | None = Field(default=None)
    tags: Any = Field(default=None, sa_column=Column(JSON, nullable=True))
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )


class ReportFeedback(SQLModel, table=True):
    """Per-report feedback (multi-axis 1-5 rating + comment & tags)."""

    __tablename__ = "report_feedback"
    __table_args__ = (
        UniqueConstraint("report_uuid", "user_uuid", name="uq_rpt_fb_user"),
    )

    uuid: uuidpkg.UUID = Field(default_factory=uuidpkg.uuid4, primary_key=True)
    report_uuid: uuidpkg.UUID = Field(
        sa_column=Column(
            "report_uuid",
            ForeignKey("report.uuid", ondelete="CASCADE"),
            nullable=False,
            index=True,
        )
    )
    user_uuid: uuidpkg.UUID = Field(
        sa_column=Column(
            "user_uuid",
            ForeignKey("user.uuid", ondelete="CASCADE"),
            nullable=False,
            index=True,
        )
    )
    overall_rating: int = Field(default=0)  # 1-5
    accuracy_rating: int | None = Field(default=None)
    completeness_rating: int | None = Field(default=None)
    usefulness_rating: int | None = Field(default=None)
    comment: str | None = Field(default=None)
    tags: Any = Field(default=None, sa_column=Column(JSON, nullable=True))
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )


# ---------------------------------------------------------------------------
# Repository
# ---------------------------------------------------------------------------


class FeedbackRepository:
    def __init__(self, db: DBCtx):
        self._db = db

    # -- Message feedback ---------------------------------------------------

    async def create_message_feedback(self, fb: MessageFeedback) -> MessageFeedback:
        async with self._db.session(writable=True) as session:
            session.add(fb)
            await session.commit()
            await session.refresh(fb)
            return fb

    async def get_message_feedback(
        self, message_uuid: uuidpkg.UUID
    ) -> Sequence[MessageFeedback]:
        async with self._db.session() as session:
            result = await session.exec(
                select(MessageFeedback).where(
                    MessageFeedback.message_uuid == message_uuid
                )
            )
            return result.all()

    async def get_message_feedback_by_id(
        self, uuid: uuidpkg.UUID
    ) -> MessageFeedback | None:
        async with self._db.session() as session:
            result = await session.exec(
                select(MessageFeedback).where(MessageFeedback.uuid == uuid).limit(1)
            )
            return result.one_or_none()

    async def update_message_feedback(
        self, uuid: uuidpkg.UUID, **kwargs: Any
    ) -> MessageFeedback | None:
        async with self._db.session(writable=True) as session:
            result = await session.exec(
                select(MessageFeedback).where(MessageFeedback.uuid == uuid).limit(1)
            )
            fb = result.one_or_none()
            if not fb:
                return None
            for k, v in kwargs.items():
                if hasattr(fb, k):
                    setattr(fb, k, v)
            fb.updated_at = datetime.now(timezone.utc)
            session.add(fb)
            await session.commit()
            await session.refresh(fb)
            return fb

    async def delete_message_feedback(self, uuid: uuidpkg.UUID) -> bool:
        async with self._db.session(writable=True) as session:
            result = await session.exec(
                select(MessageFeedback).where(MessageFeedback.uuid == uuid).limit(1)
            )
            fb = result.one_or_none()
            if not fb:
                return False
            await session.delete(fb)
            await session.commit()
            return True

    # -- Report feedback ----------------------------------------------------

    async def create_report_feedback(self, fb: ReportFeedback) -> ReportFeedback:
        async with self._db.session(writable=True) as session:
            session.add(fb)
            await session.commit()
            await session.refresh(fb)
            return fb

    async def get_report_feedback(
        self, report_uuid: uuidpkg.UUID
    ) -> Sequence[ReportFeedback]:
        async with self._db.session() as session:
            result = await session.exec(
                select(ReportFeedback).where(ReportFeedback.report_uuid == report_uuid)
            )
            return result.all()

    async def update_report_feedback(
        self, uuid: uuidpkg.UUID, **kwargs: Any
    ) -> ReportFeedback | None:
        async with self._db.session(writable=True) as session:
            result = await session.exec(
                select(ReportFeedback).where(ReportFeedback.uuid == uuid).limit(1)
            )
            fb = result.one_or_none()
            if not fb:
                return None
            for k, v in kwargs.items():
                if hasattr(fb, k):
                    setattr(fb, k, v)
            session.add(fb)
            await session.commit()
            await session.refresh(fb)
            return fb

    # -- Summary (used by agent feedback tool) ------------------------------

    async def get_feedback_summary(
        self, report_type: str | None = None, limit: int = 20
    ) -> dict[str, Any]:
        """Aggregate recent feedback for the agent to consume."""
        async with self._db.session() as session:
            # Message feedback
            msg_q = (
                select(MessageFeedback)
                .order_by(
                    MessageFeedback.created_at.desc()  # type: ignore[union-attr]
                )
                .limit(limit)
            )
            msg_result = await session.exec(msg_q)
            msg_feedbacks = msg_result.all()

            # Report feedback
            rpt_q = (
                select(ReportFeedback)
                .order_by(
                    ReportFeedback.created_at.desc()  # type: ignore[union-attr]
                )
                .limit(limit)
            )
            rpt_result = await session.exec(rpt_q)
            rpt_feedbacks = rpt_result.all()

        # Compute tag frequencies
        tag_counts: dict[str, int] = {}
        for fb in msg_feedbacks:
            if fb.tags:
                for tag in fb.tags:
                    tag_counts[tag] = tag_counts.get(tag, 0) + 1
        for fb in rpt_feedbacks:
            if fb.tags:
                for tag in fb.tags:
                    tag_counts[tag] = tag_counts.get(tag, 0) + 1

        # Compute averages
        msg_ratings = [fb.rating for fb in msg_feedbacks]
        rpt_ratings = [fb.overall_rating for fb in rpt_feedbacks if fb.overall_rating]

        return {
            "message_feedback_count": len(msg_feedbacks),
            "report_feedback_count": len(rpt_feedbacks),
            "message_avg_rating": (
                sum(msg_ratings) / len(msg_ratings) if msg_ratings else None
            ),
            "report_avg_rating": (
                sum(rpt_ratings) / len(rpt_ratings) if rpt_ratings else None
            ),
            "top_tags": sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[
                :10
            ],
            "recent_comments": [fb.comment for fb in msg_feedbacks if fb.comment][:5]
            + [fb.comment for fb in rpt_feedbacks if fb.comment][:5],
        }
