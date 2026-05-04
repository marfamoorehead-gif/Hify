from collections.abc import AsyncGenerator
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, SmallInteger, func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from hify.core.config import settings

engine = create_async_engine(
    settings.MYSQL_DSN,
    pool_size=settings.MYSQL_POOL_SIZE,
    max_overflow=settings.MYSQL_MAX_OVERFLOW,
    pool_recycle=settings.MYSQL_POOL_RECYCLE,
    pool_pre_ping=True,
    echo=False,
)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """ORM 基类。"""


class TimestampModel(Base):
    """通用字段基类：id、created_at、updated_at、deleted。

    - created_at / updated_at：数据库自动填充（server_default=func.now()）
    - updated_at：ORM 更新时自动刷新（onupdate=func.now()）
    - deleted：逻辑删除标记（0=正常，1=已删除），select_active() 自动过滤
    """

    __abstract__ = True

    id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False,
    )  # onupdate 仅对 ORM 模型属性修改生效，bulk update 需手动设置
    deleted: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, default=0, server_default="0",
    )

    @classmethod
    def select_active(cls):
        """返回 select 语句，自动过滤 deleted=0（逻辑删除）。"""
        return select(cls).where(cls.deleted == 0)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """依赖注入：每次请求创建 Session，成功 commit，异常 rollback。"""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
