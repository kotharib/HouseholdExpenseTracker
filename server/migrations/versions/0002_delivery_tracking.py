"""Add daily delivery tracking columns to milk/newspaper deliveries."""
import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "milk_deliveries",
        sa.Column("is_delivered", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.add_column(
        "newspaper_deliveries",
        sa.Column("date", sa.Date(), nullable=False, server_default=sa.text("(date('now'))")),
    )
    op.add_column(
        "newspaper_deliveries",
        sa.Column("delivery_status", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.create_index("ix_newspaper_deliveries_date", "newspaper_deliveries", ["date"])


def downgrade() -> None:
    op.drop_index("ix_newspaper_deliveries_date", table_name="newspaper_deliveries")
    op.drop_column("newspaper_deliveries", "delivery_status")
    op.drop_column("newspaper_deliveries", "date")
    op.drop_column("milk_deliveries", "is_delivered")
