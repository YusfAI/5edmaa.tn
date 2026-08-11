"""Initial MySQL schema — mirrors backend/database/schema.sql

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-08-11
"""
from alembic import op
import sqlalchemy as sa

revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None

MYSQL_TABLE_KWARGS = {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"}


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("phone", sa.String(20), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("role", sa.Enum("worker", "client", "admin", name="user_role"), nullable=False),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        **MYSQL_TABLE_KWARGS,
    )

    op.create_table(
        "worker_profiles",
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("bio", sa.Text, nullable=True),
        sa.Column("categories", sa.JSON, nullable=True),
        sa.Column("hourly_rate", sa.DECIMAL(10, 2), nullable=True),
        sa.Column("location", sa.String(100), nullable=True),
        sa.Column("availability", sa.JSON, nullable=True),
        sa.Column("portfolio_urls", sa.JSON, nullable=True),
        sa.Column("verified", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("status", sa.Enum("pending", "approved", "rejected", name="verification_status"), nullable=False, server_default="pending"),
        sa.Column("rejection_reason", sa.Text, nullable=True),
        sa.Column("premium_until", sa.DateTime, nullable=True),
        sa.Column("rating", sa.DECIMAL(3, 2), nullable=True),
        **MYSQL_TABLE_KWARGS,
    )

    op.create_table(
        "client_profiles",
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("company_name", sa.String(255), nullable=True),
        sa.Column("location", sa.String(100), nullable=True),
        sa.Column("full_name", sa.String(255), nullable=True),
        sa.Column("bio", sa.Text, nullable=True),
        sa.Column("verified", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("status", sa.Enum("pending", "approved", "rejected", name="verification_status"), nullable=False, server_default="pending"),
        sa.Column("rejection_reason", sa.Text, nullable=True),
        **MYSQL_TABLE_KWARGS,
    )

    op.create_table(
        "job_offers",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("client_id", sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("category", sa.String(100), nullable=False, index=True),
        sa.Column("location", sa.String(100), nullable=False, index=True),
        sa.Column("budget_min", sa.DECIMAL(10, 2), nullable=True),
        sa.Column("budget_max", sa.DECIMAL(10, 2), nullable=True),
        sa.Column("status", sa.Enum("open", "closed", name="job_status"), nullable=False, server_default="open"),
        sa.Column("boost_until", sa.DateTime, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        **MYSQL_TABLE_KWARGS,
    )

    op.create_table(
        "job_applications",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("job_id", sa.Integer, sa.ForeignKey("job_offers.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("worker_id", sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("cover_message", sa.Text, nullable=True),
        sa.Column("status", sa.Enum("pending", "accepted", "rejected", name="application_status"), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        **MYSQL_TABLE_KWARGS,
    )

    op.create_table(
        "services",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("provider_id", sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("category", sa.String(100), nullable=False, index=True),
        sa.Column("location", sa.String(100), nullable=False, index=True),
        sa.Column("base_price", sa.DECIMAL(10, 2), nullable=True),
        sa.Column("is_premium", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        **MYSQL_TABLE_KWARGS,
    )

    op.create_table(
        "bookings",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("service_id", sa.Integer, sa.ForeignKey("services.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("customer_id", sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("provider_id", sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("scheduled_for", sa.DateTime, nullable=False),
        sa.Column("status", sa.Enum("pending", "confirmed", "cancelled", "completed", name="booking_status"), nullable=False, server_default="pending"),
        sa.Column("note", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        **MYSQL_TABLE_KWARGS,
    )

    op.create_table(
        "reviews",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("booking_id", sa.Integer, sa.ForeignKey("bookings.id", ondelete="CASCADE"), nullable=True, index=True),
        sa.Column("job_application_id", sa.Integer, sa.ForeignKey("job_applications.id", ondelete="CASCADE"), nullable=True, index=True),
        sa.Column("reviewer_id", sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("reviewee_id", sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("rating", sa.SmallInteger, nullable=False),
        sa.Column("comment", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("rating BETWEEN 1 AND 5", name="chk_reviews_rating"),
        **MYSQL_TABLE_KWARGS,
    )

    op.create_table(
        "wallets",
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("balance", sa.DECIMAL(10, 2), nullable=False, server_default="0.00"),
        sa.Column("currency", sa.String(3), nullable=False, server_default="TND"),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        **MYSQL_TABLE_KWARGS,
    )

    op.create_table(
        "transactions",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("type", sa.Enum("topup", "payment", "withdrawal", "refund", "fee", "release", name="transaction_type"), nullable=False),
        sa.Column("amount", sa.DECIMAL(10, 2), nullable=False),
        sa.Column("status", sa.Enum("pending", "completed", "failed", "cancelled", name="transaction_status"), nullable=False, server_default="pending"),
        sa.Column("reference", sa.String(255), nullable=True),
        sa.Column("description", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        **MYSQL_TABLE_KWARGS,
    )

    op.create_table(
        "messages",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("job_id", sa.Integer, sa.ForeignKey("job_offers.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("sender_id", sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("receiver_id", sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("attachments", sa.JSON, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column("read_at", sa.DateTime, nullable=True),
        **MYSQL_TABLE_KWARGS,
    )

    op.create_table(
        "subscription_plans",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.String(255), nullable=True),
        sa.Column("price", sa.DECIMAL(10, 2), nullable=False),
        sa.Column("duration_days", sa.Integer, nullable=False),
        sa.Column("features", sa.JSON, nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        **MYSQL_TABLE_KWARGS,
    )

    op.create_table(
        "user_subscriptions",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("plan_id", sa.Integer, sa.ForeignKey("subscription_plans.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("start_date", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column("end_date", sa.DateTime, nullable=False),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        **MYSQL_TABLE_KWARGS,
    )

    op.create_table(
        "job_boosts",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("job_id", sa.Integer, sa.ForeignKey("job_offers.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("boost_type", sa.String(50), nullable=False),
        sa.Column("start_date", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column("end_date", sa.DateTime, nullable=False),
        sa.Column("price_paid", sa.DECIMAL(10, 2), nullable=False),
        **MYSQL_TABLE_KWARGS,
    )


def downgrade() -> None:
    op.drop_table("job_boosts")
    op.drop_table("user_subscriptions")
    op.drop_table("subscription_plans")
    op.drop_table("messages")
    op.drop_table("transactions")
    op.drop_table("wallets")
    op.drop_table("reviews")
    op.drop_table("bookings")
    op.drop_table("services")
    op.drop_table("job_applications")
    op.drop_table("job_offers")
    op.drop_table("client_profiles")
    op.drop_table("worker_profiles")
    op.drop_table("users")
