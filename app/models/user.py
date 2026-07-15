import enum

from sqlalchemy import Boolean, Enum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db.databases import Base
from app.core.db.models import TimestampMixin


class Department(str, enum.Enum):
    DEVELOPER = "developer"
    MEDICAL_TEAM = "medical team"
    RESEARCHER = "researcher"


class Gender(str, enum.Enum):
    MALE = "male"
    FEMALE = "female"


class UserRole(str, enum.Enum):
    PENDING = "pending"
    STAFF = "staff"
    ADMIN = "admin"


def enum_values(enum_cls: type[enum.Enum]) -> list[str]:
    return [member.value for member in enum_cls]


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    department: Mapped[Department] = mapped_column(Enum(Department, values_callable=enum_values), nullable=False)
    gender: Mapped[Gender] = mapped_column(Enum(Gender, values_callable=enum_values), nullable=False)
    phone_number: Mapped[str] = mapped_column(String(20), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, values_callable=enum_values),
        nullable=False,
        default=UserRole.PENDING,
        server_default=UserRole.PENDING.value,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="1")

    medical_records: Mapped[list["MedicalRecord"]] = relationship(back_populates="creator")
    analyses: Mapped[list["AIAnalysis"]] = relationship(back_populates="creator")
