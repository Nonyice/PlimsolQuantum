"""Add commercial subscription billing and audit entities."""
from alembic import op
import sqlalchemy as sa

revision = "08_subscription_billing"
down_revision = "07_create_positions_table"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("subscription_plans", sa.Column("currency", sa.String(length=3), nullable=False, server_default="USD"))

    op.create_table(
        "payments",
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("plan_id", sa.UUID(), nullable=False),
        sa.Column("subscription_id", sa.UUID(), nullable=True),
        sa.Column("amount", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="USD"),
        sa.Column("method", sa.String(length=30), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="PENDING"),
        sa.Column("reference", sa.String(length=120), nullable=False),
        sa.Column("provider_reference", sa.String(length=120), nullable=True),
        sa.Column("evidence_path", sa.String(length=500), nullable=True),
        sa.Column("evidence_original_name", sa.String(length=255), nullable=True),
        sa.Column("rejection_reason", sa.Text(), nullable=True),
        sa.Column("admin_notes", sa.Text(), nullable=True),
        sa.Column("paid_at", sa.DateTime(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(), nullable=True),
        sa.Column("reviewed_by", sa.UUID(), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["plan_id"], ["subscription_plans.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["subscription_id"], ["subscriptions.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["reviewed_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("id"),
        sa.UniqueConstraint("reference"),
    )
    op.create_index("ix_payments_user_id", "payments", ["user_id"])
    op.create_index("ix_payments_plan_id", "payments", ["plan_id"])
    op.create_index("ix_payments_subscription_id", "payments", ["subscription_id"])
    op.create_index("ix_payments_status", "payments", ["status"])
    op.create_index("ix_payments_reference", "payments", ["reference"])
    op.create_index("ix_payments_provider_reference", "payments", ["provider_reference"])

    op.create_table(
        "audit_logs",
        sa.Column("actor_id", sa.UUID(), nullable=True),
        sa.Column("target_user_id", sa.UUID(), nullable=True),
        sa.Column("action", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("metadata_json", sa.Text(), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["actor_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["target_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("id"),
    )
    op.create_index("ix_audit_logs_actor_id", "audit_logs", ["actor_id"])
    op.create_index("ix_audit_logs_target_user_id", "audit_logs", ["target_user_id"])
    op.create_index("ix_audit_logs_action", "audit_logs", ["action"])

    # Seed the three commercial PQI plans. Existing rows are updated by name.
    op.execute("""
        INSERT INTO subscription_plans
            (name, description, currency, price, duration_days, max_bots, max_exchanges,
             max_trading_pairs, paper_trading, live_trading, priority_support, api_access,
             is_trial, active, id, created_at, updated_at, deleted_at, is_active)
        VALUES
            ('Starter', '30-day PQI subscription', 'USD', 50.00, 30, 4, 2, 20, true, true, false, false, false, true, '11111111-1111-4111-8111-111111111111', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, NULL, true),
            ('Professional', '180-day PQI subscription', 'USD', 200.00, 180, 4, 2, 20, true, true, true, false, false, true, '22222222-2222-4222-8222-222222222222', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, NULL, true),
            ('Enterprise', '12-month PQI subscription', 'USD', 300.00, 365, 4, 2, 20, true, true, true, true, false, true, '33333333-3333-4333-8333-333333333333', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, NULL, true)
        ON CONFLICT (name) DO UPDATE SET
            description = EXCLUDED.description, currency = EXCLUDED.currency, price = EXCLUDED.price,
            duration_days = EXCLUDED.duration_days, live_trading = EXCLUDED.live_trading,
            priority_support = EXCLUDED.priority_support, api_access = EXCLUDED.api_access, active = true;
    """)


def downgrade():
    op.drop_index("ix_audit_logs_action", table_name="audit_logs")
    op.drop_index("ix_audit_logs_target_user_id", table_name="audit_logs")
    op.drop_index("ix_audit_logs_actor_id", table_name="audit_logs")
    op.drop_table("audit_logs")
    op.drop_index("ix_payments_provider_reference", table_name="payments")
    op.drop_index("ix_payments_reference", table_name="payments")
    op.drop_index("ix_payments_status", table_name="payments")
    op.drop_index("ix_payments_subscription_id", table_name="payments")
    op.drop_index("ix_payments_plan_id", table_name="payments")
    op.drop_index("ix_payments_user_id", table_name="payments")
    op.drop_table("payments")
    op.drop_column("subscription_plans", "currency")
