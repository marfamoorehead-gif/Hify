from sqlalchemy.ext.asyncio import AsyncSession


class AgentService:
    """Agent 业务逻辑。"""

    def __init__(self, db: AsyncSession):
        self.db = db
