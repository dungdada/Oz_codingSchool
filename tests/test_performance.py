from types import SimpleNamespace

import pytest
from starlette.responses import JSONResponse

from app.core.performance import observe_api_performance


@pytest.mark.anyio
async def test_api_response_includes_server_timing_header():
    request = SimpleNamespace(
        url=SimpleNamespace(path="/api/v1/users/me"),
        method="GET",
    )

    async def call_next(_request):
        return JSONResponse({"ok": True})

    response = await observe_api_performance(request, call_next)

    assert response.headers["Server-Timing"].startswith("app;dur=")


@pytest.mark.anyio
async def test_static_response_does_not_include_server_timing_header():
    request = SimpleNamespace(
        url=SimpleNamespace(path="/static/app.js"),
        method="GET",
    )

    async def call_next(_request):
        return JSONResponse({"ok": True})

    response = await observe_api_performance(request, call_next)

    assert "Server-Timing" not in response.headers
