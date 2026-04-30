from hify.core.exceptions import ErrorCode, HifyBaseException


class AgentNotFoundError(HifyBaseException):
    def __init__(self, agent_id: int):
        super().__init__(
            code=ErrorCode.RESOURCE_NOT_FOUND,
            message=f"Agent not found: {agent_id}",
        )
