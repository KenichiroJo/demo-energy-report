"""add_feedback_and_report_tables

Revision ID: b1a3c5d7e9f2
Revises: 4d5262be920d
Create Date: 2026-04-13 10:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b1a3c5d7e9f2"
down_revision: Union[str, Sequence[str], None] = "4d5262be920d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create report, message_feedback, report_feedback tables."""

    # -- report table --
    op.create_table(
        "report",
        sa.Column("uuid", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(), nullable=False, server_default=""),
        sa.Column("content", sa.Text(), nullable=False, server_default=""),
        sa.Column(
            "report_type", sa.String(), nullable=False, server_default="composite"
        ),
        sa.Column("summary", sa.String(), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column("user_uuid", sa.Uuid(), nullable=True),
        sa.Column("chat_uuid", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("uuid", name=op.f("pk_report")),
        sa.ForeignKeyConstraint(
            ["user_uuid"],
            ["user.uuid"],
            name=op.f("fk_report_user_uuid_user"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["chat_uuid"],
            ["chat.uuid"],
            name=op.f("fk_report_chat_uuid_chat"),
            ondelete="SET NULL",
        ),
    )
    op.create_index(op.f("ix_report_user_uuid"), "report", ["user_uuid"])

    # -- message_feedback table --
    op.create_table(
        "message_feedback",
        sa.Column("uuid", sa.Uuid(), nullable=False),
        sa.Column("message_uuid", sa.Uuid(), nullable=False),
        sa.Column("user_uuid", sa.Uuid(), nullable=False),
        sa.Column("rating", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("comment", sa.String(), nullable=True),
        sa.Column("tags", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("uuid", name=op.f("pk_message_feedback")),
        sa.ForeignKeyConstraint(
            ["message_uuid"],
            ["message.uuid"],
            name=op.f("fk_message_feedback_message_uuid_message"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_uuid"],
            ["user.uuid"],
            name=op.f("fk_message_feedback_user_uuid_user"),
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint("message_uuid", "user_uuid", name="uq_msg_fb_user"),
    )
    op.create_index(
        op.f("ix_message_feedback_message_uuid"),
        "message_feedback",
        ["message_uuid"],
    )
    op.create_index(
        op.f("ix_message_feedback_user_uuid"),
        "message_feedback",
        ["user_uuid"],
    )

    # -- report_feedback table --
    op.create_table(
        "report_feedback",
        sa.Column("uuid", sa.Uuid(), nullable=False),
        sa.Column("report_uuid", sa.Uuid(), nullable=False),
        sa.Column("user_uuid", sa.Uuid(), nullable=False),
        sa.Column("overall_rating", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("accuracy_rating", sa.Integer(), nullable=True),
        sa.Column("completeness_rating", sa.Integer(), nullable=True),
        sa.Column("usefulness_rating", sa.Integer(), nullable=True),
        sa.Column("comment", sa.String(), nullable=True),
        sa.Column("tags", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("uuid", name=op.f("pk_report_feedback")),
        sa.ForeignKeyConstraint(
            ["report_uuid"],
            ["report.uuid"],
            name=op.f("fk_report_feedback_report_uuid_report"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_uuid"],
            ["user.uuid"],
            name=op.f("fk_report_feedback_user_uuid_user"),
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint("report_uuid", "user_uuid", name="uq_rpt_fb_user"),
    )
    op.create_index(
        op.f("ix_report_feedback_report_uuid"),
        "report_feedback",
        ["report_uuid"],
    )
    op.create_index(
        op.f("ix_report_feedback_user_uuid"),
        "report_feedback",
        ["user_uuid"],
    )


def downgrade() -> None:
    """Drop feedback and report tables."""
    op.drop_table("report_feedback")
    op.drop_table("message_feedback")
    op.drop_table("report")
