import time

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from hify.shared.logging import generate_trace_id, get_logger

logger = get_logger(__name__)


class TraceIdMiddleware(BaseHTTPMiddleware):
    """每个请求生成 trace_id，注入日志上下文，记录请求耗时。"""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        trace_id = generate_trace_id()
        start = time.perf_counter()

        response = await call_next(request)

        duration_ms = round((time.perf_counter() - start) * 1000)
        logger.info(
            "request",
            trace_id=trace_id,
            method=request.method,
            path=request.url.path,
            status=response.status_code,
            duration_ms=duration_ms,
        )
        response.headers["X-Trace-Id"] = trace_id
        return response
