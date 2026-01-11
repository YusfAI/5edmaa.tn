from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "a2fb4b850fa4"
down_revision = "f3d33e4ef143"  # keep whatever was here originally
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create enum type for roles (PostgreSQL enum)
    user_role_enum = sa.Enum("worker", "client", "admin", name="user_role")
    user_role_enum.create(op.get_bind(), checkfirst=True)

    # Add role column to existing users table
    op.add_column(
        "users",
        sa.Column(
            "role",
            user_role_enum,
            nullable=False,
            server_default="worker",  # default for existing rows
        ),
    )

    # Optional: remove default so future inserts must set role explicitly
    op.alter_column("users", "role", server_default=None)


def downgrade() -> None:
    # Remove column
    op.drop_column("users", "role")

    # Drop enum type
    user_role_enum = sa.Enum("worker", "client", "admin", name="user_role")
    user_role_enum.drop(op.get_bind(), checkfirst=True)
