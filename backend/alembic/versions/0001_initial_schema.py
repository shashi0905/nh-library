"""initial_schema

Revision ID: 0001
Revises:
Create Date: 2026-05-15
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    """Create books, members, loans tables and tsvector trigger."""
    # ── books ─────────────────────────────────────────────────────────────────
    op.create_table(
        "books",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("isbn", sa.String(13), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("author", sa.String(255), nullable=False),
        sa.Column("total_copies", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("available", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("search_vector", postgresql.TSVECTOR(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("isbn", name="uq_books_isbn"),
    )
    op.create_index("ix_books_isbn", "books", ["isbn"], unique=True)
    op.create_index(
        "ix_books_search_vector",
        "books",
        ["search_vector"],
        postgresql_using="gin",
    )

    # ── members ───────────────────────────────────────────────────────────────
    op.create_table(
        "members",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("phone", sa.String(20), nullable=True),
        sa.Column(
            "joined_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("email", name="uq_members_email"),
    )
    op.create_index("ix_members_email", "members", ["email"], unique=True)

    # ── loans ─────────────────────────────────────────────────────────────────
    op.create_table(
        "loans",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("book_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("member_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "borrowed_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("due_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("returned_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "status",
            sa.Enum("ACTIVE", "RETURNED", "OVERDUE", name="loanstatus"),
            nullable=False,
            server_default="ACTIVE",
        ),
        sa.Column("fine_amount", sa.Numeric(10, 2), nullable=True),
        sa.Column("fine_paid", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["book_id"], ["books.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["member_id"], ["members.id"], ondelete="RESTRICT"),
    )
    op.create_index("ix_loans_member_status", "loans", ["member_id", "status"])
    op.create_index("ix_loans_due_date", "loans", ["due_date"])

    # ── tsvector trigger ──────────────────────────────────────────────────────
    op.execute("""
        CREATE FUNCTION books_search_vector_update() RETURNS trigger AS $$
        BEGIN
            NEW.search_vector :=
                setweight(to_tsvector('english', coalesce(NEW.title, '')), 'A') ||
                setweight(to_tsvector('english', coalesce(NEW.author, '')), 'B');
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)
    op.execute("""
        CREATE TRIGGER books_search_vector_trigger
        BEFORE INSERT OR UPDATE ON books
        FOR EACH ROW EXECUTE FUNCTION books_search_vector_update();
    """)

    # ── updated_at trigger ────────────────────────────────────────────────────
    op.execute("""
        CREATE FUNCTION set_updated_at() RETURNS trigger AS $$
        BEGIN
            NEW.updated_at = now();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)
    for table in ("books", "members"):
        op.execute(f"""
            CREATE TRIGGER set_{table}_updated_at
            BEFORE UPDATE ON {table}
            FOR EACH ROW EXECUTE FUNCTION set_updated_at();
        """)


def downgrade() -> None:
    """Drop all tables, indexes, triggers, and functions."""
    for table in ("books", "members"):
        op.execute(f"DROP TRIGGER IF EXISTS set_{table}_updated_at ON {table}")
    op.execute("DROP TRIGGER IF EXISTS books_search_vector_trigger ON books")
    op.execute("DROP FUNCTION IF EXISTS books_search_vector_update")
    op.execute("DROP FUNCTION IF EXISTS set_updated_at")

    op.drop_table("loans")
    op.drop_table("members")
    op.drop_table("books")
    op.execute("DROP TYPE IF EXISTS loanstatus")
