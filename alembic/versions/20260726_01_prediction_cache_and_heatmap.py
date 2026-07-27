"""add prediction cache constraint and heatmap URL

Revision ID: 20260726_01
Revises: 20260715_01
Create Date: 2026-07-26 00:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "20260726_01"
down_revision: Union[str, Sequence[str], None] = "20260715_01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "ai_analyses",
        sa.Column(
            "heatmap_image_url",
            sa.String(length=500),
            nullable=True,
        ),
    )

    # 기존에 같은 진료기록과 모델로 저장된 중복 결과가 있다면
    # 가장 먼저 생성된 결과 하나만 유지한다.
    op.execute(
        """
        DELETE newer
        FROM ai_analyses AS newer
        INNER JOIN ai_analyses AS older
            ON newer.medical_record_id = older.medical_record_id
            AND newer.ai_model = older.ai_model
            AND newer.id > older.id
        """
    )
    op.create_unique_constraint(
        "uq_ai_analyses_record_model",
        "ai_analyses",
        ["medical_record_id", "ai_model"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_ai_analyses_record_model",
        "ai_analyses",
        type_="unique",
    )
    op.drop_column("ai_analyses", "heatmap_image_url")
