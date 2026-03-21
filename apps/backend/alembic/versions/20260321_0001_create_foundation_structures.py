"""Create foundational schemas and technical tables.

This migration intentionally avoids business marts/features/serving logic.
"""

import sqlalchemy as sa

from alembic import op

revision = "202603210001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    for schema_name in ("clean", "mart", "feature", "serving"):
        op.execute(f"CREATE SCHEMA IF NOT EXISTS {schema_name}")

    op.create_table(
        "job_runs",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("job_name", sa.String(length=100), nullable=False),
        sa.Column("layer", sa.String(length=50), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column(
            "started_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        schema="public",
    )
    op.create_index("ix_job_runs_job_name", "job_runs", ["job_name"], schema="public")
    op.create_index("ix_job_runs_status", "job_runs", ["status"], schema="public")

    op.create_table(
        "source_files",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("source_name", sa.String(length=100), nullable=False),
        sa.Column("file_path", sa.String(length=500), nullable=False),
        sa.Column("file_hash", sa.String(length=128), nullable=True),
        sa.Column("detected_encoding", sa.String(length=64), nullable=True),
        sa.Column(
            "ingestion_status", sa.String(length=50), nullable=False, server_default="discovered"
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        schema="public",
    )
    op.create_index("ix_source_files_source_name", "source_files", ["source_name"], schema="public")
    op.create_index(
        "ux_source_files_file_path", "source_files", ["file_path"], unique=True, schema="public"
    )

    op.create_table(
        "model_registry",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("model_name", sa.String(length=100), nullable=False),
        sa.Column("model_version", sa.String(length=50), nullable=False),
        sa.Column("stage", sa.String(length=50), nullable=False),
        sa.Column("artifact_path", sa.String(length=500), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        schema="serving",
    )
    op.create_index(
        "ix_model_registry_model_name",
        "model_registry",
        ["model_name"],
        schema="serving",
    )
    op.create_index(
        "ux_model_registry_model_version",
        "model_registry",
        ["model_name", "model_version"],
        unique=True,
        schema="serving",
    )


def downgrade() -> None:
    op.drop_index("ux_model_registry_model_version", table_name="model_registry", schema="serving")
    op.drop_index("ix_model_registry_model_name", table_name="model_registry", schema="serving")
    op.drop_table("model_registry", schema="serving")

    op.drop_index("ux_source_files_file_path", table_name="source_files", schema="public")
    op.drop_index("ix_source_files_source_name", table_name="source_files", schema="public")
    op.drop_table("source_files", schema="public")

    op.drop_index("ix_job_runs_status", table_name="job_runs", schema="public")
    op.drop_index("ix_job_runs_job_name", table_name="job_runs", schema="public")
    op.drop_table("job_runs", schema="public")

    for schema_name in ("serving", "feature", "mart", "clean"):
        op.execute(f"DROP SCHEMA IF EXISTS {schema_name}")
