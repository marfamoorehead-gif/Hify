from hify.core.exceptions import ErrorCode, HifyBaseException


class ProviderNotFoundError(HifyBaseException):
    def __init__(self, provider_id: int):
        super().__init__(
            code=ErrorCode.PROVIDER_NOT_FOUND,
            message=f"Model provider not found: {provider_id}",
        )


class LLMRateLimitError(HifyBaseException):
    def __init__(self, detail: str = "LLM rate limit exceeded"):
        super().__init__(code=ErrorCode.LLM_RATE_LIMIT, message=detail)


class LLMServiceUnavailableError(HifyBaseException):
    def __init__(self, detail: str = "LLM service unavailable"):
        super().__init__(code=ErrorCode.LLM_SERVICE_UNAVAILABLE, message=detail)


class LLMTimeoutError(HifyBaseException):
    def __init__(self, detail: str = "LLM request timeout"):
        super().__init__(code=ErrorCode.LLM_TIMEOUT, message=detail)
