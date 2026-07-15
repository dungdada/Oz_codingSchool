"""create health domain tables

Revision ID: 20260715_01
Revises:
Create Date: 2026-07-15 00:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "20260715_01"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password", sa.String(length=255), nullable=False),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.Column("department", sa.Enum("developer", "medical team", "researcher", name="department"), nullable=False),
        sa.Column("gender", sa.Enum("male", "female", name="gender"), nullable=False),
        sa.Column("phone_number", sa.String(length=20), nullable=False),
        sa.Column("role", sa.Enum("pending", "staff", "admin", name="userrole"), server_default="pending", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="1", nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("current_timestamp(0)"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("current_timestamp(0)"), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)

    op.create_table(
        "patients",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.Column("age", sa.Integer(), nullable=False),
        sa.Column("gender", sa.Enum("male", "female", name="gender"), nullable=False),
        sa.Column("phone_number", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("current_timestamp(0)"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("current_timestamp(0)"), nullable=True),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), server_default="0", nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_patients_gender"), "patients", ["gender"], unique=False)
    op.create_index(op.f("ix_patients_name"), "patients", ["name"], unique=False)

    op.create_table(
        "medical_records",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("patient_id", sa.Integer(), nullable=False),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("chart_number", sa.String(length=50), nullable=False),
        sa.Column("symptoms", sa.Text(), nullable=False),
        sa.Column("xray_image_url", sa.String(length=500), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("current_timestamp(0)"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("current_timestamp(0)"), nullable=True),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_medical_records_chart_number"), "medical_records", ["chart_number"], unique=True)
    op.create_index(op.f("ix_medical_records_patient_id"), "medical_records", ["patient_id"], unique=False)

    op.create_table(
        "ai_analyses",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("medical_record_id", sa.Integer(), nullable=False),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("is_pneumonia", sa.Boolean(), nullable=False),
        sa.Column("confidence", sa.DECIMAL(precision=5, scale=2), nullable=False),
        sa.Column("ai_model", sa.String(length=100), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("current_timestamp(0)"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("current_timestamp(0)"), nullable=True),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["medical_record_id"], ["medical_records.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_ai_analyses_medical_record_id"), "ai_analyses", ["medical_record_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_ai_analyses_medical_record_id"), table_name="ai_analyses")
    op.drop_table("ai_analyses")
    op.drop_index(op.f("ix_medical_records_patient_id"), table_name="medical_records")
    op.drop_index(op.f("ix_medical_records_chart_number"), table_name="medical_records")
    op.drop_table("medical_records")
    op.drop_index(op.f("ix_patients_name"), table_name="patients")
    op.drop_index(op.f("ix_patients_gender"), table_name="patients")
    op.drop_table("patients")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")
