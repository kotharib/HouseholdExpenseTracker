"""Initial schema for household management & expense tracking."""
import sqlalchemy as sa
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("username", sa.String(64), nullable=False),
        sa.Column("password_hash", sa.String(256), nullable=False),
        sa.Column("role", sa.String(16), nullable=False, server_default="user"),
        sa.UniqueConstraint("username"),
    )
    op.create_index("ix_users_username", "users", ["username"])

    op.create_table(
        "expenses",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("category", sa.String(64), nullable=False),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("notes", sa.String(512), nullable=True),
        sa.Column("payment_mode", sa.String(32), nullable=True, server_default="cash"),
        sa.Column("tags", sa.String(256), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_expenses_category", "expenses", ["category"])
    op.create_index("ix_expenses_date", "expenses", ["date"])

    op.create_table(
        "servants",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("role", sa.String(64), nullable=False, server_default="home cleaning"),
        sa.Column("monthly_salary", sa.Float(), nullable=False),
        sa.Column("payment_status", sa.String(16), nullable=False, server_default="pending"),
        sa.Column("attendance_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_servants_name", "servants", ["name"])

    op.create_table(
        "milk_deliveries",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("supplier", sa.String(128), nullable=False),
        sa.Column("quantity", sa.Float(), nullable=False),
        sa.Column("rate", sa.Float(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("month", sa.String(7), nullable=False),
        sa.Column("payment_status", sa.String(16), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_milk_deliveries_supplier", "milk_deliveries", ["supplier"])
    op.create_index("ix_milk_deliveries_month", "milk_deliveries", ["month"])

    op.create_table(
        "newspaper_deliveries",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("monthly_cost", sa.Float(), nullable=False),
        sa.Column("month", sa.String(7), nullable=False),
        sa.Column("payment_status", sa.String(16), nullable=False, server_default="pending"),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_newspaper_deliveries_name", "newspaper_deliveries", ["name"])
    op.create_index("ix_newspaper_deliveries_month", "newspaper_deliveries", ["month"])


def downgrade() -> None:
    op.drop_table("newspaper_deliveries")
    op.drop_table("milk_deliveries")
    op.drop_table("servants")
    op.drop_table("expenses")
    op.drop_table("users")
