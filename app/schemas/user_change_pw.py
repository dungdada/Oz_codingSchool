from pydantic import BaseModel, Field, field_validator, model_validator

from app.schemas.user import validate_password_rules


class UserPasswordUpdateRequest(BaseModel):
    current_password: str = Field(
        ...,
        min_length=8,
        max_length=64,
        description="현재 비밀번호",
    )
    new_password: str = Field(
        ...,
        min_length=8,
        max_length=64,
        description="새 비밀번호",
    )

    @field_validator("new_password")
    @classmethod
    def check_new_password(cls, value: str) -> str:
        return validate_password_rules(value)

    @model_validator(mode="after")
    def check_password_change(self):
        if self.current_password == self.new_password:
            raise ValueError(
                "새 비밀번호는 현재 비밀번호와 달라야 합니다."
            )

        return self