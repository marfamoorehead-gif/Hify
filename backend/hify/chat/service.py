from sqlalchemy.ext.asyncio import AsyncSession


class ChatService:
    """对话引擎业务逻辑。"""

    def __init__(self, db: AsyncSession):
        self.db = db
