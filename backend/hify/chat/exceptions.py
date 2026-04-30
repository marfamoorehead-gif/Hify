from hify.core.exceptions import ErrorCode, HifyBaseException


class ConversationNotFoundError(HifyBaseException):
    def __init__(self, conversation_id: int):
        super().__init__(
            code=ErrorCode.RESOURCE_NOT_FOUND,
            message=f"Conversation not found: {conversation_id}",
        )
