from decimal import Decimal

from sqlalchemy import Boolean, DECIMAL, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db.databases import Base
from app.core.db.models import TimestampMixin


class AIAnalysis(Base, TimestampMixin):
    __tablename__ = "ai_analyses"
    __table_args__ = (
        UniqueConstraint(
            "medical_record_id",
            "ai_model",
            name="uq_ai_analyses_record_model",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    medical_record_id: Mapped[int] = mapped_column(
        ForeignKey("medical_records.id", ondelete="CASCADE"), nullable=False, index=True
    )
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    is_pneumonia: Mapped[bool] = mapped_column(Boolean, nullable=False)
    confidence: Mapped[Decimal] = mapped_column(DECIMAL(5, 2), nullable=False)
    ai_model: Mapped[str] = mapped_column(String(100), nullable=False)
    heatmap_image_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    medical_record: Mapped["MedicalRecord"] = relationship(back_populates="analyses")
    creator: Mapped["User | None"] = relationship(back_populates="analyses")
