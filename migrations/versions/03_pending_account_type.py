"""Use pending account type until onboarding choice is made."""

from alembic import op
import sqlalchemy as sa

revision = "03_pending_account_type"
down_revision = "02a533528db6"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column(
        "users",
        "account_type",
        existing_type=sa.String(length=20),
        server_default=sa.text("'pending'"),
    )
    op.execute(
        "UPDATE users SET account_type = 'pending' "
        "WHERE onboarding_completed = false"
    )


def downgrade():
    op.alter_column(
        "users",
        "account_type",
        existing_type=sa.String(length=20),
        server_default=sa.text("'trial'"),
    )
