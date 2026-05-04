from hify.core.exceptions import BizException, ErrorCode


class ProviderNotFoundError(BizException):
    def __init__(self, provider_id: int):
        super().__init__(
            ErrorCode.PROVIDER_NOT_FOUND,
            message=f"Model provider not found: {provider_id}",
        )


class LLMRateLimitError(BizException):
    def __init__(self, detail: str | None = None):
        super().__init__(ErrorCode.LLM_RATE_LIMIT, message=detail)


class LLMServiceUnavailableError(BizException):
    def __init__(self, detail: str | None = None):
        super().__init__(ErrorCode.LLM_SERVICE_UNAVAILABLE, message=detail)


class LLMTimeoutError(BizException):
    def __init__(self, detail: str | None = None):
        super().__init__(ErrorCode.LLM_TIMEOUT, message=detail)
