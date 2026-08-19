"""Create the missing PQI trading positions table.

The Position ORM model is present, but existing databases do not have the
corresponding table. PQI therefore fails immediately after producing a
trade decision when it checks for an OPEN position.

Revision ID: 07_create_positions_table
Revises: 06_fix_pqi_pair_last_update, 06_pqi_pair_last_update_not_null
"""

from alembic import op
import sqlalchemy as sa


revision = "07_create_positions_table"
down_revision = (
    "06_fix_pqi_pair_last_update",
    "06_pqi_pair_last_update_not_null",
)
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "positions",
        sa.Column("trading_account_id", sa.UUID(), nullable=False),
        sa.Column("symbol", sa.String(length=20), nullable=False),
        sa.Column("side", sa.String(length=10), nullable=False),
        sa.Column("quantity", sa.Float(), nullable=False),
        sa.Column("entry_price", sa.Float(), nullable=False),
        sa.Column("exit_price", sa.Float(), nullable=True),
        sa.Column("stop_loss", sa.Float(), nullable=False),
        sa.Column("take_profit", sa.Float(), nullable=False),
        sa.Column(
            "status",
            sa.String(length=20),
            nullable=False,
            server_default="OPEN",
        ),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(
            ["trading_account_id"],
            ["trading_accounts.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("id"),
    )

    with op.batch_alter_table("positions", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_positions_trading_account_id"),
            ["trading_account_id"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix_positions_status"),
            ["status"],
            unique=False,
        )


def downgrade():
    op.drop_table("positions")
