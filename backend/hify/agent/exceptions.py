from hify.core.exceptions import BizException, ErrorCode


class AgentNotFoundError(BizException):
    def __init__(self, agent_id: int):
        super().__init__(
            ErrorCode.RESOURCE_NOT_FOUND,
            message=f"Agent not found: {agent_id}",
        )
