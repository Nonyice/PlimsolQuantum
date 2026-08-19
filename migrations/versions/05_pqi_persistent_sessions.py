"""Add persistent PQI sessions and up to three monitored pairs per session."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "05_pqi_persistent_sessions"
down_revision = "04_trial_paper_capital"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "pqi_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("mode", sa.String(20), nullable=False, server_default="trial"),
        sa.Column("exchange", sa.String(30), nullable=False),
        sa.Column("exchange_id", sa.String(120), nullable=True),
        sa.Column("market_type", sa.String(20), nullable=False, server_default="spot"),
        sa.Column("capital", sa.Numeric(18, 8), nullable=False, server_default="1000"),
        sa.Column("status", sa.String(20), nullable=False, server_default="ACTIVE"),
        sa.Column("started_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("last_heartbeat", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("stopped_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_pqi_sessions_user_id", "pqi_sessions", ["user_id"])
    op.create_index("ix_pqi_sessions_status", "pqi_sessions", ["status"])

    op.create_table(
        "pqi_session_pairs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("symbol", sa.String(30), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="OBSERVING"),
        sa.Column("side", sa.String(10), nullable=True),
        sa.Column("entry_price", sa.Numeric(20, 10), nullable=True),
        sa.Column("mark_price", sa.Numeric(20, 10), nullable=True),
        sa.Column("quantity", sa.Numeric(20, 10), nullable=True),
        sa.Column("notional", sa.Numeric(20, 10), nullable=True),
        sa.Column("stop_loss", sa.Numeric(20, 10), nullable=True),
        sa.Column("take_profit", sa.Numeric(20, 10), nullable=True),
        sa.Column("pnl", sa.Numeric(20, 10), nullable=False, server_default="0"),
        sa.Column("opened_at", sa.DateTime(), nullable=True),
        sa.Column("closed_at", sa.DateTime(), nullable=True),
        sa.Column("last_update", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["session_id"], ["pqi_sessions.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_pqi_session_pairs_session_id", "pqi_session_pairs", ["session_id"])
    op.create_index("ix_pqi_session_pairs_symbol", "pqi_session_pairs", ["symbol"])
    op.create_index("ix_pqi_session_pairs_status", "pqi_session_pairs", ["status"])


def downgrade():
    op.drop_table("pqi_session_pairs")
    op.drop_table("pqi_sessions")
