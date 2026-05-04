from enum import Enum

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from hify.shared.logging import get_logger
from hify.shared.schemas import Result

logger = get_logger(__name__)


# ── 错误码分段 ──
# 40000-40999：请求参数 / 业务逻辑错误
# 41000-41999：认证授权错误
# 42000-42999：LLM / Provider 相关错误
# 43000-43999：工作流执行错误
# 44000-44999：知识库 / RAG 相关错误
# 45000-45999：工具调用相关错误
# 50000-50999：系统内部错误（兜底）


class ErrorCode(Enum):
    """错误码枚举，每项包含 code 和默认 message。"""

    # 40000-40999：请求参数 / 业务逻辑
    BAD_REQUEST = (40000, "Bad request")
    RESOURCE_NOT_FOUND = (40001, "Resource not found")
    RESOURCE_ALREADY_EXISTS = (40002, "Resource already exists")
    OPERATION_FAILED = (40003, "Operation failed")
    PARAM_VALIDATION_FAILED = (40004, "Parameter validation failed")

    # 41000-41999：认证授权
    UNAUTHORIZED = (41001, "Unauthorized")
    TOKEN_EXPIRED = (41002, "Token expired")
    PERMISSION_DENIED = (41003, "Permission denied")

    # 42000-42999：LLM / Provider
    PROVIDER_NOT_FOUND = (42001, "Model provider not found")
    LLM_RATE_LIMIT = (42002, "LLM rate limit exceeded")
    LLM_SERVICE_UNAVAILABLE = (42003, "LLM service unavailable")
    LLM_TIMEOUT = (42004, "LLM request timeout")
    LLM_AUTH_FAILED = (42005, "LLM authentication failed")
    LLM_BAD_REQUEST = (42006, "LLM bad request")

    # 43000-43999：工作流
    WORKFLOW_NOT_FOUND = (43001, "Workflow not found")
    WORKFLOW_EXECUTION_ERROR = (43002, "Workflow execution failed")
    WORKFLOW_NODE_ERROR = (43003, "Workflow node error")
    WORKFLOW_CYCLE_DETECTED = (43004, "Workflow cycle detected")

    # 44000-44999：知识库 / RAG
    KNOWLEDGE_NOT_FOUND = (44001, "Knowledge base not found")
    DOCUMENT_IMPORT_ERROR = (44002, "Document import failed")
    DOCUMENT_NOT_FOUND = (44003, "Document not found")
    EMBEDDING_ERROR = (44004, "Embedding failed")

    # 45000-45999：工具调用
    TOOL_NOT_FOUND = (45001, "Tool not found")
    TOOL_EXECUTION_ERROR = (45002, "Tool execution failed")
    TOOL_SCHEMA_PARSE_ERROR = (45003, "Invalid tool schema")

    # 50000-50999：系统内部
    INTERNAL_ERROR = (50000, "Internal server error")

    def __init__(self, code: int, message: str):
        self.code = code
        self.message = message


class BizException(Exception):
    """业务异常，持有 ErrorCode，支持自定义 message 覆盖。"""

    def __init__(self, error_code: ErrorCode, message: str | None = None):
        self.error_code = error_code
        self.code = error_code.code
        self.message = message or error_code.message
        super().__init__(self.message)


# ── 全局异常处理器 ──


def _to_http_status(code: int) -> int:
    """业务错误码 → HTTP 状态码映射。"""
    if 40000 <= code <= 40999:
        return 400
    if 41000 <= code <= 41999:
        if code in (41001, 41002):  # UNAUTHORIZED, TOKEN_EXPIRED
            return 401
        return 403  # PERMISSION_DENIED
    if 42000 <= code <= 42999:
        if code == 42002:  # RATE_LIMIT
            return 429
        if code == 42003:  # SERVICE_UNAVAILABLE
            return 502
        if code == 42004:  # TIMEOUT
            return 504
        if code == 42001:  # PROVIDER_NOT_FOUND
            return 404
        return 400
    if 43000 <= code <= 43999:
        if code == 43001:  # WORKFLOW_NOT_FOUND
            return 404
        return 500
    if 44000 <= code <= 44999:
        if code in (44001, 44003):  # KNOWLEDGE_NOT_FOUND, DOCUMENT_NOT_FOUND
            return 404
        return 400
    if 45000 <= code <= 45999:
        if code == 45001:  # TOOL_NOT_FOUND
            return 404
        return 400
    return 500


async def _biz_exception_handler(
    request: Request,
    exc: BizException,
) -> JSONResponse:
    """捕获 BizException，返回对应错误码和 HTTP 状态码。"""
    logger.warning(
        "business exception",
        code=exc.code,
        message=exc.message,
        path=request.url.path,
        method=request.method,
    )
    http_status = _to_http_status(exc.code)
    result = Result.fail(code=exc.code, message=exc.message)
    return JSONResponse(status_code=http_status, content=result.model_dump())


async def _validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """捕获参数校验异常，返回校验错误详情。"""
    errors = exc.errors()
    details = "; ".join(
        f"{'.'.join(str(loc) for loc in e['loc'])}: {e['msg']}" for e in errors
    )
    logger.warning(
        "validation error",
        path=request.url.path,
        method=request.method,
        details=details,
    )
    ec = ErrorCode.PARAM_VALIDATION_FAILED
    result = Result.fail(code=ec.code, message=f"{ec.message}: {details}")
    return JSONResponse(status_code=422, content=result.model_dump())


async def _unhandled_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """兜底捕获 Exception，返回系统内部错误。"""
    logger.error(
        "unhandled exception",
        error=str(exc),
        error_type=type(exc).__name__,
        path=request.url.path,
        method=request.method,
    )
    ec = ErrorCode.INTERNAL_ERROR
    result = Result.fail(code=ec.code, message=ec.message)
    return JSONResponse(status_code=500, content=result.model_dump())


def register_exception_handlers(app: FastAPI) -> None:
    """注册全局异常处理器。"""
    app.add_exception_handler(BizException, _biz_exception_handler)
    app.add_exception_handler(RequestValidationError, _validation_exception_handler)
    app.add_exception_handler(Exception, _unhandled_exception_handler)
