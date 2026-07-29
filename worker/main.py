import json
import socket
import time
import uuid
from pathlib import Path

import redis

from worker.config import settings
from worker.model import predict_pneumonia
from worker.redis_client import get_redis

CONSUMER_NAME = f"{socket.gethostname()}-{uuid.uuid4().hex[:8]}"


def ensure_consumer_group(client: redis.Redis) -> None:
    try:
        client.xgroup_create(
            name=settings.REDIS_STREAM_KEY,
            groupname=settings.REDIS_CONSUMER_GROUP,
            id="0",
            mkstream=True,
        )
        print(f"[worker] consumer group '{settings.REDIS_CONSUMER_GROUP}' 생성됨")
    except redis.ResponseError as exc:
        if "BUSYGROUP" not in str(exc):
            raise
        # 이미 다른 워커(또는 이전 실행)가 그룹을 만들어둔 경우 -> 정상, 그냥 계속 진행


def process_message(client: redis.Redis, message_id: str, fields: dict) -> None:
    task_id = fields["task_id"]
    channel = fields["channel"]
    image_path = Path(fields["image_path"])

    try:
        prediction = predict_pneumonia(image_path)
        payload = {
            "task_id": task_id,
            "record_id": int(fields["record_id"]),
            "ai_model": fields["ai_model"],
            "is_pneumonia": prediction.is_pneumonia,
            "confidence": prediction.confidence,
            "error": None,
        }
    except Exception as exc:  # noqa: BLE001 - 워커는 어떤 예외든 결과 채널로 보고해야 한다
        payload = {
            "task_id": task_id,
            "record_id": int(fields["record_id"]),
            "ai_model": fields["ai_model"],
            "is_pneumonia": None,
            "confidence": None,
            "error": str(exc),
        }
        print(f"[worker] 예측 실패 (task_id={task_id}): {exc}")

    client.publish(channel, json.dumps(payload))
    client.xack(settings.REDIS_STREAM_KEY, settings.REDIS_CONSUMER_GROUP, message_id)


def reclaim_stale_messages(client: redis.Redis) -> None:
    """
    비정상 종료된 워커가 ACK 못 하고 남긴 pending 메시지를,
    일정 시간(CLAIM_IDLE_MS) 이상 방치되어 있으면 이 워커가 대신 가져온다.
    """
    try:
        _next_cursor, claimed, _deleted = client.xautoclaim(
            name=settings.REDIS_STREAM_KEY,
            groupname=settings.REDIS_CONSUMER_GROUP,
            consumername=CONSUMER_NAME,
            min_idle_time=settings.CLAIM_IDLE_MS,
            start_id="0-0",
            count=10,
        )
    except redis.ResponseError:
        return
    except redis.exceptions.TimeoutError:
        # 회수할 pending 메시지가 없어 응답이 늦어진 것뿐일 수 있음 -> 다음 루프에서 재시도
        return

    for message_id, fields in claimed:
        print(f"[worker] 회수된 pending 메시지 처리: {message_id}")
        process_message(client, message_id, fields)


def run() -> None:
    client = get_redis()
    ensure_consumer_group(client)

    print("[worker] 모델 예열(warm-up) 중...")
    from worker.model import load_model
    load_model()
    print("[worker] 모델 로딩 완료")

    print(f"[worker] '{CONSUMER_NAME}' 시작, stream='{settings.REDIS_STREAM_KEY}'")

    while True:
        reclaim_stale_messages(client)

        try:
            response = client.xreadgroup(
                groupname=settings.REDIS_CONSUMER_GROUP,
                consumername=CONSUMER_NAME,
                streams={settings.REDIS_STREAM_KEY: ">"},
                count=1,
                block=5000,  # ms
            )
        except redis.exceptions.TimeoutError:
            # BLOCK 시간 동안 새 작업이 없었던 것뿐 -> 정상, 다음 루프로
            continue

        if not response:
            continue

        for _stream_key, messages in response:
            for message_id, fields in messages:
                print(f"[worker] 작업 수신: {message_id} (task_id={fields.get('task_id')})")
                process_message(client, message_id, fields)


if __name__ == "__main__":
    while True:
        try:
            run()
        except redis.ConnectionError as exc:
            print(f"[worker] Redis 연결 실패, 5초 후 재시도: {exc}")
            time.sleep(5)
