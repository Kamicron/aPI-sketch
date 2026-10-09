"""Likes et historique d'écoute

Revision ID: 0003
Revises: 0002
Create Date: 2026-10-09
"""
import sqlalchemy as sa
from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "likes",
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("sketch_id", sa.Integer(), sa.ForeignKey("sketches.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        mysql_charset="utf8mb4",
    )
    op.create_table(
        "plays",
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("sketch_id", sa.Integer(), sa.ForeignKey("sketches.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("last_played_at", sa.DateTime(), nullable=False),
        sa.Column("play_count", sa.Integer(), nullable=False, server_default="1"),
        mysql_charset="utf8mb4",
    )


def downgrade() -> None:
    op.drop_table("plays")
    op.drop_table("likes")
