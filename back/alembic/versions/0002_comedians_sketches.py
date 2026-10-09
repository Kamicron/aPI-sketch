"""Humoristes (chaînes YouTube) et sketchs découverts

Revision ID: 0002
Revises: 0001
Create Date: 2026-10-09
"""
import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "comedians",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("youtube_channel_id", sa.String(32), nullable=False, unique=True),
        sa.Column("channel_url", sa.String(300), nullable=False),
        sa.Column("subscribed", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("min_duration_s", sa.Integer(), nullable=False, server_default="120"),
        sa.Column("max_duration_s", sa.Integer(), nullable=False, server_default="1800"),
        sa.Column("last_synced_at", sa.DateTime()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        mysql_charset="utf8mb4",
    )
    op.create_table(
        "sketches",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("comedian_id", sa.Integer(), sa.ForeignKey("comedians.id", ondelete="CASCADE"), nullable=False),
        sa.Column("youtube_id", sa.String(16), nullable=False, unique=True),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("duration_s", sa.Integer()),
        sa.Column("published_at", sa.DateTime(), nullable=False),
        sa.Column("thumbnail_url", sa.String(500)),
        sa.Column("status", sa.String(16), nullable=False, server_default="discovered"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        mysql_charset="utf8mb4",
    )
    op.create_index("ix_sketches_comedian_published", "sketches", ["comedian_id", "published_at"])


def downgrade() -> None:
    op.drop_index("ix_sketches_comedian_published", table_name="sketches")
    op.drop_table("sketches")
    op.drop_table("comedians")
