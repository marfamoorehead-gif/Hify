from fastapi import Request
from fastapi.responses import JSONResponse

from hify.shared.logging import get_logger

logger = get_logger(__name__)


# ── 错误码分段 ──
# 40000-40999：请求参数 / 业务逻辑错误
# 41000-41999：认证授权错误
# 42000-42999：LLM / Provider 相关错误
# 43000-43999：工作流执行错误
# 44000-44999：知识库 / RAG 相关错误
# 45000-45999：工具调用相关错误
# 50000-50999：系统内部错误（兜底）


class ErrorCode:
    """错误码常量。"""

    # 40000-40999：请求参数 / 业务逻辑
    BAD_REQUEST = 40000
    RESOURCE_NOT_FOUND = 40001
    RESOURCE_ALREADY_EXISTS = 40002
    OPERATION_FAILED = 40003

    # 41000-41999：认证授权
    UNAUTHORIZED = 41001
    TOKEN_EXPIRED = 41002
    PERMISSION_DENIED = 41003

    # 42000-42999：LLM / Provider
    PROVIDER_NOT_FOUND = 42001
    LLM_RATE_LIMIT = 42002
    LLM_SERVICE_UNAVAILABLE = 42003
    LLM_TIMEOUT = 42004
    LLM_AUTH_FAILED = 42005
    LLM_BAD_REQUEST = 42006

    # 43000-43999：工作流
    WORKFLOW_NOT_FOUND = 43001
    WORKFLOW_EXECUTION_ERROR = 43002
    WORKFLOW_NODE_ERROR = 43003
    WORKFLOW_CYCLE_DETECTED = 43004

    # 44000-44999：知识库 / RAG
    KNOWLEDGE_NOT_FOUND = 44001
    DOCUMENT_IMPORT_ERROR = 44002
    DOCUMENT_NOT_FOUND = 44003
    EMBEDDING_ERROR = 44004

    # 45000-45999：工具调用
    TOOL_NOT_FOUND = 45001
    TOOL_EXECUTION_ERROR = 45002
    TOOL_SCHEMA_PARSE_ERROR = 45003

    # 50000-50999：系统内部
    INTERNAL_ERROR = 50000


class HifyBaseException(Exception):
    """业务异常基类。"""

    def __init__(self, code: int, message: str):
        self.code = code
        self.message = message
        super().__init__(message)


# ── 全局异常处理器 ──


async def hify_exception_handler(
    request: Request,
    exc: HifyBaseException,
) -> JSONResponse:
    """处理 HifyBaseException，返回 Result 格式响应。"""
    logger.warning(
        "business exception",
        code=exc.code,
        message=exc.message,
        path=request.url.path,
        method=request.method,
    )
    return JSONResponse(
        status_code=200,
        content={"code": exc.code, "message": exc.message, "data": None},
    )


async def unhandled_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """兜底异常处理器，返回系统内部错误。"""
    logger.error(
        "unhandled exception",
        error=str(exc),
        error_type=type(exc).__name__,
        path=request.url.path,
        method=request.method,
    )
    return JSONResponse(
        status_code=500,
        content={
            "code": ErrorCode.INTERNAL_ERROR,
            "message": "Internal server error",
            "data": None,
        },
    )
