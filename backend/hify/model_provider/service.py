from sqlalchemy.ext.asyncio import AsyncSession


class ModelProviderService:
    """模型提供商业务逻辑。"""

    def __init__(self, db: AsyncSession):
        self.db = db
