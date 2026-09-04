"""Add delivery subscriptions and nullable delivery status."""
import sqlalchemy as sa
from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "delivery_subscriptions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("delivery_type", sa.String(32), nullable=False),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("delivery_frequency", sa.String(32), nullable=False, server_default="daily"),
        sa.Column("custom_pattern", sa.String(256), nullable=True),
        sa.Column("rate_per_unit", sa.Float(), nullable=True),
        sa.Column("monthly_cost", sa.Float(), nullable=True),
        sa.Column("default_quantity", sa.Float(), nullable=True),
        sa.Column("auto_generate", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_delivery_subscriptions_user_id", "delivery_subscriptions", ["user_id"])
    op.create_index("ix_delivery_subscriptions_delivery_type", "delivery_subscriptions", ["delivery_type"])
    op.create_index("ix_delivery_subscriptions_name", "delivery_subscriptions", ["name"])

    op.create_table(
        "custom_deliveries",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("month", sa.String(7), nullable=False),
        sa.Column("delivered", sa.Boolean(), nullable=True),
        sa.Column("subscription_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_custom_deliveries_name", "custom_deliveries", ["name"])
    op.create_index("ix_custom_deliveries_date", "custom_deliveries", ["date"])
    op.create_index("ix_custom_deliveries_month", "custom_deliveries", ["month"])
    op.create_index("ix_custom_deliveries_subscription_id", "custom_deliveries", ["subscription_id"])

    with op.batch_alter_table("milk_deliveries") as batch:
        batch.add_column(sa.Column("subscription_id", sa.Integer(), nullable=True))
        batch.alter_column("is_delivered", existing_type=sa.Boolean(), nullable=True)

    with op.batch_alter_table("newspaper_deliveries") as batch:
        batch.add_column(sa.Column("subscription_id", sa.Integer(), nullable=True))
        batch.alter_column("delivery_status", existing_type=sa.Boolean(), nullable=True)

    op.create_index("ix_milk_deliveries_subscription_id", "milk_deliveries", ["subscription_id"])
    op.create_index("ix_newspaper_deliveries_subscription_id", "newspaper_deliveries", ["subscription_id"])


def downgrade() -> None:
    op.drop_index("ix_newspaper_deliveries_subscription_id", table_name="newspaper_deliveries")
    op.drop_index("ix_milk_deliveries_subscription_id", table_name="milk_deliveries")
    with op.batch_alter_table("newspaper_deliveries") as batch:
        batch.drop_column("subscription_id")
        batch.alter_column("delivery_status", existing_type=sa.Boolean(), nullable=False)
    with op.batch_alter_table("milk_deliveries") as batch:
        batch.drop_column("subscription_id")
        batch.alter_column("is_delivered", existing_type=sa.Boolean(), nullable=False)
    op.drop_table("custom_deliveries")
    op.drop_table("delivery_subscriptions")
