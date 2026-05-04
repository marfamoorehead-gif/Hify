from hify.core.exceptions import BizException, ErrorCode


class WorkflowNotFoundError(BizException):
    def __init__(self, workflow_id: int):
        super().__init__(
            ErrorCode.WORKFLOW_NOT_FOUND,
            message=f"Workflow not found: {workflow_id}",
        )


class WorkflowExecutionError(BizException):
    def __init__(self, detail: str | None = None):
        super().__init__(ErrorCode.WORKFLOW_EXECUTION_ERROR, message=detail)


class WorkflowNodeError(BizException):
    def __init__(self, node_type: str, detail: str = ""):
        super().__init__(
            ErrorCode.WORKFLOW_NODE_ERROR,
            message=f"Workflow node error [{node_type}]: {detail}",
        )
