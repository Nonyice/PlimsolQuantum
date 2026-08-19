"""sync pqi sessions schema

Revision ID: a3d6a6479b67
Revises: 05_pqi_persistent_sessions
Create Date: 2026-08-17 12:11:23.451249

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "a3d6a6479b67"
down_revision = "05_pqi_persistent_sessions"
branch_labels = None
depends_on = None


def upgrade():
    # ---------------------------------------------------------
    # pqi_sessions
    # ---------------------------------------------------------
    with op.batch_alter_table("pqi_sessions", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "created_at",
                sa.DateTime(),
                nullable=True,
            )
        )

        batch_op.add_column(
            sa.Column(
                "updated_at",
                sa.DateTime(),
                nullable=True,
            )
        )

        batch_op.add_column(
            sa.Column(
                "deleted_at",
                sa.DateTime(),
                nullable=True,
            )
        )

        batch_op.add_column(
            sa.Column(
                "is_active",
                sa.Boolean(),
                nullable=True,
            )
        )

    # Populate existing sessions.
    op.execute(
        """
        UPDATE pqi_sessions
        SET
            created_at = COALESCE(started_at, CURRENT_TIMESTAMP),
            updated_at = COALESCE(last_heartbeat, started_at, CURRENT_TIMESTAMP),
            is_active = CASE
                WHEN status = 'ACTIVE' THEN TRUE
                ELSE FALSE
            END
        WHERE created_at IS NULL
           OR updated_at IS NULL
           OR is_active IS NULL
        """
    )

    # Make required fields NOT NULL after existing records
    # have been populated.
    with op.batch_alter_table("pqi_sessions", schema=None) as batch_op:
        batch_op.alter_column(
            "created_at",
            existing_type=sa.DateTime(),
            nullable=False,
        )

        batch_op.alter_column(
            "updated_at",
            existing_type=sa.DateTime(),
            nullable=False,
        )

        batch_op.alter_column(
            "is_active",
            existing_type=sa.Boolean(),
            nullable=False,
        )

        batch_op.create_index(
            "ix_pqi_sessions_created_at",
            ["created_at"],
            unique=False,
        )

        batch_op.create_index(
            "ix_pqi_sessions_mode",
            ["mode"],
            unique=False,
        )

    # ---------------------------------------------------------
    # pqi_session_pairs
    # ---------------------------------------------------------
    with op.batch_alter_table("pqi_session_pairs", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "created_at",
                sa.DateTime(),
                nullable=True,
            )
        )

        batch_op.add_column(
            sa.Column(
                "updated_at",
                sa.DateTime(),
                nullable=True,
            )
        )

        batch_op.add_column(
            sa.Column(
                "deleted_at",
                sa.DateTime(),
                nullable=True,
            )
        )

        batch_op.add_column(
            sa.Column(
                "is_active",
                sa.Boolean(),
                nullable=True,
            )
        )

    # Populate existing pair records.
    op.execute(
        """
        UPDATE pqi_session_pairs
        SET
            created_at = CURRENT_TIMESTAMP,
            updated_at = CURRENT_TIMESTAMP,
            is_active = TRUE
        WHERE created_at IS NULL
           OR updated_at IS NULL
           OR is_active IS NULL
        """
    )

    with op.batch_alter_table("pqi_session_pairs", schema=None) as batch_op:
        batch_op.alter_column(
            "created_at",
            existing_type=sa.DateTime(),
            nullable=False,
        )

        batch_op.alter_column(
            "updated_at",
            existing_type=sa.DateTime(),
            nullable=False,
        )

        batch_op.alter_column(
            "is_active",
            existing_type=sa.Boolean(),
            nullable=False,
        )

        batch_op.create_index(
            "ix_pqi_session_pairs_created_at",
            ["created_at"],
            unique=False,
        )

    # ---------------------------------------------------------
    # trials
    # ---------------------------------------------------------
    #
    # Do not remove the existing trials index as part of this
    # schema repair. It is unrelated to the current PQI error.
    #
    pass


def downgrade():
    with op.batch_alter_table("pqi_session_pairs", schema=None) as batch_op:
        batch_op.drop_index("ix_pqi_session_pairs_created_at")

        batch_op.drop_column("is_active")
        batch_op.drop_column("deleted_at")
        batch_op.drop_column("updated_at")
        batch_op.drop_column("created_at")

    with op.batch_alter_table("pqi_sessions", schema=None) as batch_op:
        batch_op.drop_index("ix_pqi_sessions_mode")
        batch_op.drop_index("ix_pqi_sessions_created_at")

        batch_op.drop_column("is_active")
        batch_op.drop_column("deleted_at")
        batch_op.drop_column("updated_at")
        batch_op.drop_column("created_at")