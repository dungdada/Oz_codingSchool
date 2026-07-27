import logging
from time import perf_counter
from typing import Awaitable, Callable

from fastapi import Request, Response

from app.core.config import settings

logger = logging.getLogger(__name__)


async def observe_api_performance(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    started_at = perf_counter()
    response = await call_next(request)
    elapsed = perf_counter() - started_at

    if request.url.path.startswith("/api/"):
        response.headers["Server-Timing"] = (
            f'app;dur={elapsed * 1000:.2f}'
        )
        if elapsed > settings.API_SLOW_REQUEST_SECONDS:
            logger.warning(
                "Slow API request method=%s path=%s elapsed=%.3fs",
                request.method,
                request.url.path,
                elapsed,
            )

    return response
