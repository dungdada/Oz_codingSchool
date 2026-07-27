from pydantic import BaseModel, Field, field_validator, model_validator

from app.models.user import Department
from app.schemas.user import validate_phone_number


class UserProfileUpdateRequest(BaseModel):
    department: Department | None = Field(
        default=None,
        description="변경할 부서",
    )
    phone_number: str | None = Field(
        default=None,
        description="변경할 휴대폰 번호",
    )

    @field_validator("phone_number")
    @classmethod
    def check_phone_number(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return value

        return validate_phone_number(value)

    @model_validator(mode="after")
    def check_update_fields(self):
        # 빈 JSON 요청 차단: {}
        if not self.model_fields_set:
            raise ValueError(
                "수정할 항목을 하나 이상 입력해야 합니다."
            )

        # 명시적인 null 요청 차단
        # 예: {"department": null}
        for field_name in self.model_fields_set:
            if getattr(self, field_name) is None:
                raise ValueError(
                    f"{field_name}에는 null을 입력할 수 없습니다."
                )

        return self