from hify.core.exceptions import ErrorCode, HifyBaseException


class WorkflowNotFoundError(HifyBaseException):
    def __init__(self, workflow_id: int):
        super().__init__(
            code=ErrorCode.WORKFLOW_NOT_FOUND,
            message=f"Workflow not found: {workflow_id}",
        )


class WorkflowExecutionError(HifyBaseException):
    def __init__(self, detail: str = "Workflow execution failed"):
        super().__init__(code=ErrorCode.WORKFLOW_EXECUTION_ERROR, message=detail)


class WorkflowNodeError(HifyBaseException):
    def __init__(self, node_type: str, detail: str = ""):
        super().__init__(
            code=ErrorCode.WORKFLOW_NODE_ERROR,
            message=f"Workflow node error [{node_type}]: {detail}",
        )
