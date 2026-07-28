import json
import time
import uuid
from typing import Any

import redis.asyncio as aioredis

from app.core.config import settings

_redis: aioredis.Redis | None = None


def get_redis() -> aioredis.Redis:
    """
    프로세스 전역에서 하나의 커넥션 풀을 재사용한다.
    FastAPI Depends()로 주입해서 쓸 수도 있지만, 여기서는 서비스 계층에서 직접 호출한다.
    """
    global _redis
    if _redis is None:
        _redis = aioredis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            decode_responses=True,
        )
    return _redis


def _result_channel(task_id: str) -> str:
    return f"prediction:result:{task_id}"


def _lock_key(record_id: int, ai_model: str) -> str:
    return f"prediction:lock:{record_id}:{ai_model}"


async def enqueue_prediction_task(
    *,
    record_id: int,
    ai_model: str,
    image_path: str,
    lock_ttl_seconds: int,
) -> tuple[str, bool]:
    """
    예측 작업을 Redis Stream에 등록한다.

    동일 (record_id, ai_model) 조합에 대해 이미 처리 중인 작업이 있으면
    새로 등록하지 않고, 기존 작업과 같은 task_id를 반환한다. (동시 요청 중복 방지)

    반환값: (task_id, 새로 등록했는지 여부)
    """
    client = get_redis()
    task_id = str(uuid.uuid4())
    lock_key = _lock_key(record_id, ai_model)

    # SET NX: 락을 획득한 요청만 실제로 작업을 큐에 등록한다.
    acquired = await client.set(lock_key, task_id, nx=True, ex=lock_ttl_seconds)
    if not acquired:
        # 이미 같은 예측이 진행 중 -> 그 작업의 task_id를 그대로 사용해 같이 기다린다.
        existing_task_id = await client.get(lock_key)
        return existing_task_id or task_id, False

    await client.xadd(
        settings.REDIS_STREAM_KEY,
        {
            "task_id": task_id,
            "record_id": str(record_id),
            "ai_model": ai_model,
            "image_path": image_path,
            "channel": _result_channel(task_id),
            "enqueued_at": str(time.time()),
        },
    )
    return task_id, True


async def wait_for_prediction_result(
    task_id: str,
    timeout_seconds: float,
) -> dict[str, Any] | None:
    """
    워커가 Pub/Sub 채널에 결과를 발행할 때까지 기다린다.
    timeout 안에 못 받으면 None을 반환한다.
    """
    client = get_redis()
    pubsub = client.pubsub()
    channel = _result_channel(task_id)
    await pubsub.subscribe(channel)

    try:
        deadline = time.monotonic() + timeout_seconds
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return None
            message = await pubsub.get_message(
                ignore_subscribe_messages=True,
                timeout=min(remaining, 0.5),
            )
            if message is None:
                continue
            return json.loads(message["data"])
    finally:
        await pubsub.unsubscribe(channel)
        await pubsub.aclose()
