from hify.core.exceptions import BizException, ErrorCode


class ConversationNotFoundError(BizException):
    def __init__(self, conversation_id: int):
        super().__init__(
            ErrorCode.RESOURCE_NOT_FOUND,
            message=f"Conversation not found: {conversation_id}",
        )
