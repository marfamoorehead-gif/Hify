from sqlalchemy.ext.asyncio import AsyncSession


class ToolService:
    """工具集成业务逻辑。"""

    def __init__(self, db: AsyncSession):
        self.db = db
