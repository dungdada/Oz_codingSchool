import redis

from worker.config import settings


def get_redis() -> redis.Redis:
    return redis.Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        decode_responses=True,
        # xreadgroup(block=...)로 오래 대기하는 커맨드가 있으므로,
        # 소켓 자체 타임아웃은 그보다 훨씬 넉넉하게 잡아야 한다.
        # (짧으면 Windows에서 정상적인 블로킹 대기 중에도 TimeoutError가 난다)
        socket_timeout=30,
        socket_connect_timeout=10,
    )
