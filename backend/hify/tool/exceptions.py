from hify.core.exceptions import BizException, ErrorCode


class ToolNotFoundError(BizException):
    def __init__(self, tool_id: int):
        super().__init__(
            ErrorCode.TOOL_NOT_FOUND,
            message=f"Tool not found: {tool_id}",
        )


class ToolExecutionError(BizException):
    def __init__(self, detail: str | None = None):
        super().__init__(ErrorCode.TOOL_EXECUTION_ERROR, message=detail)


class ToolSchemaParseError(BizException):
    def __init__(self, detail: str | None = None):
        super().__init__(ErrorCode.TOOL_SCHEMA_PARSE_ERROR, message=detail)
