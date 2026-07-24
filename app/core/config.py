from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DB_USER: str = "root"
    DB_PASSWORD: str = "password1234"
    DB_HOST: str = "localhost"
    DB_PORT: str = "3306"
    DB_NAME: str = "ai_health"
    JWT_SECRET_KEY: str | None = None
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    COOKIE_SECURE: bool = False
    AI_MODEL_PATH: str = "app/ml/final_seed42_best8_full_model.pth"
    AI_MODEL_NAME: str = "final-seed42-best8-efficientnet"
    AI_IMAGE_SIZE: int = 224
    AI_PNEUMONIA_CLASS_INDEX: int = 1
    AI_DECISION_THRESHOLD: float = 0.5

    model_config = {
        "env_file": ".env",
        "extra": "ignore"
    }


settings = Settings()
