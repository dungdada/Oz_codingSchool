from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db.databases import Base
from app.core.db.models import TimestampMixin


class MedicalRecord(Base, TimestampMixin):
    __tablename__ = "medical_records"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    chart_number: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    symptoms: Mapped[str] = mapped_column(Text, nullable=False)
    xray_image_url: Mapped[str] = mapped_column(String(500), nullable=False)

    patient: Mapped["Patient"] = relationship(back_populates="medical_records")
    creator: Mapped["User | None"] = relationship(back_populates="medical_records")
    analyses: Mapped[list["AIAnalysis"]] = relationship(back_populates="medical_record", cascade="all, delete-orphan")
