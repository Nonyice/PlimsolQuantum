"""Add selectable paper trading capital to trials."""
from alembic import op
import sqlalchemy as sa

revision = "04_trial_paper_capital"
down_revision = "03_pending_account_type"
branch_labels = None
depends_on = None

def upgrade():
    op.add_column("trials", sa.Column("paper_capital", sa.Numeric(18, 8), nullable=False, server_default=sa.text("10000")))

def downgrade():
    op.drop_column("trials", "paper_capital")
