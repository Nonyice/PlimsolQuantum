"""Repair PQI pair heartbeat column for persistent sessions.

Existing deployments created pqi_session_pairs.last_update as NOT NULL while
the ORM model allowed NULL. New pair creation could therefore fail during
PQI engagement.
"""
from alembic import op
import sqlalchemy as sa

revision = "06_pqi_pair_last_update_not_null"
down_revision = "a3d6a6479b67"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        """
        UPDATE pqi_session_pairs
        SET last_update = COALESCE(last_update, updated_at, created_at, CURRENT_TIMESTAMP)
        WHERE last_update IS NULL
        """
    )

    with op.batch_alter_table("pqi_session_pairs", schema=None) as batch_op:
        batch_op.alter_column(
            "last_update",
            existing_type=sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        )


def downgrade():
    with op.batch_alter_table("pqi_session_pairs", schema=None) as batch_op:
        batch_op.alter_column(
            "last_update",
            existing_type=sa.DateTime(),
            nullable=True,
            server_default=None,
        )
