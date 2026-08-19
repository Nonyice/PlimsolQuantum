"""Repair PQI session-pair last_update constraint/default."""
from alembic import op
import sqlalchemy as sa

revision = "06_fix_pqi_pair_last_update"
down_revision = "a3d6a6479b67"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("UPDATE pqi_session_pairs SET last_update = COALESCE(last_update, updated_at, created_at, CURRENT_TIMESTAMP) WHERE last_update IS NULL")
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
            nullable=False,
            server_default=None,
        )
