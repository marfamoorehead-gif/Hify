from hify.core.exceptions import ErrorCode, HifyBaseException


class ToolNotFoundError(HifyBaseException):
    def __init__(self, tool_id: int):
        super().__init__(
            code=ErrorCode.TOOL_NOT_FOUND,
            message=f"Tool not found: {tool_id}",
        )


class ToolExecutionError(HifyBaseException):
    def __init__(self, detail: str = "Tool execution failed"):
        super().__init__(code=ErrorCode.TOOL_EXECUTION_ERROR, message=detail)


class ToolSchemaParseError(HifyBaseException):
    def __init__(self, detail: str = "Invalid OpenAPI schema"):
        super().__init__(code=ErrorCode.TOOL_SCHEMA_PARSE_ERROR, message=detail)
