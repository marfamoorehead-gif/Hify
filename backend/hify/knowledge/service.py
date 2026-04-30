from sqlalchemy.ext.asyncio import AsyncSession


class KnowledgeService:
    """知识库业务逻辑。"""

    def __init__(self, db: AsyncSession):
        self.db = db
