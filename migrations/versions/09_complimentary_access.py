"""Add auditable complimentary subscription access."""
from alembic import op
import sqlalchemy as sa

revision = "09_complimentary_access"
down_revision = "08_subscription_billing"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("subscriptions", sa.Column("access_type", sa.String(length=20), nullable=False, server_default="PAID"))
    op.add_column("subscriptions", sa.Column("granted_by", sa.UUID(), nullable=True))
    op.add_column("subscriptions", sa.Column("grant_reason", sa.Text(), nullable=True))
    op.add_column("subscriptions", sa.Column("revoked_at", sa.DateTime(), nullable=True))
    op.create_foreign_key("fk_subscriptions_granted_by_users", "subscriptions", "users", ["granted_by"], ["id"], ondelete="SET NULL")
    op.create_index("ix_subscriptions_access_type", "subscriptions", ["access_type"])
    op.create_index("ix_subscriptions_granted_by", "subscriptions", ["granted_by"])
    op.alter_column("subscriptions", "access_type", server_default=None)


def downgrade():
    op.drop_index("ix_subscriptions_granted_by", table_name="subscriptions")
    op.drop_index("ix_subscriptions_access_type", table_name="subscriptions")
    op.drop_constraint("fk_subscriptions_granted_by_users", "subscriptions", type_="foreignkey")
    op.drop_column("subscriptions", "revoked_at")
    op.drop_column("subscriptions", "grant_reason")
    op.drop_column("subscriptions", "granted_by")
    op.drop_column("subscriptions", "access_type")
