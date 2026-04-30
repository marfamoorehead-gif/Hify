from sqlalchemy.ext.asyncio import AsyncSession


class WorkflowService:
    """工作流业务逻辑。"""

    def __init__(self, db: AsyncSession):
        self.db = db
