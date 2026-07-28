from pydantic_settings import BaseSettings


class WorkerSettings(BaseSettings):
    """
    AI 워커는 FastAPI 앱(app/)과 완전히 분리된 배포 단위이므로,
    app.core.config를 가져다 쓰지 않고 필요한 설정만 독립적으로 정의한다.
    같은 .env 파일을 공유해서 값을 읽는다.
    """

    AI_MODEL_PATH: str = "worker/models/final_seed42_best8_weights_only.pth"
    AI_MODEL_ARCHITECTURE: str = "efficientnet_b0"
    AI_MODEL_NUM_CLASSES: int = 2
    AI_MODEL_NAME: str = "final-seed42-best8-efficientnet"
    AI_IMAGE_SIZE: int = 224
    AI_PNEUMONIA_CLASS_INDEX: int = 1
    AI_DECISION_THRESHOLD: float = 0.5

    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_STREAM_KEY: str = "prediction:tasks"
    REDIS_CONSUMER_GROUP: str = "prediction-workers"

    # 처리 중 워커가 죽었을 때, 이 시간(ms) 이상 응답 없는 pending 메시지는
    # 다른 워커가 대신 가져갈 수 있도록 회수 대상으로 본다. (비정상 종료 복구용)
    CLAIM_IDLE_MS: int = 30_000

    model_config = {
        "env_file": ".env",
        "extra": "ignore",
    }


settings = WorkerSettings()
