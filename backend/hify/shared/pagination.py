from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from hify.shared.schemas import PageResult


async def paginate(
    db: AsyncSession,
    model,
    *,
    page: int = 1,
    page_size: int = 20,
    filters=None,
) -> PageResult:
    """偏移分页：第一页查 total + 数据，后续页只查数据。

    用法:
        result = await paginate(db, App, page=1, page_size=20)
        result = await paginate(db, App, filters=[App.owner_id == user_id])
    """
    query = model.select_active()
    if filters:
        for f in filters:
            query = query.where(f)

    # 查 total
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    # 查数据
    offset = (page - 1) * page_size
    items = (
        await db.execute(query.offset(offset).limit(page_size))
    ).scalars().all()

    return PageResult(
        data=items,
        total=total,
        page=page,
        page_size=page_size,
    )


async def cursor_paginate(
    db: AsyncSession,
    model,
    *,
    after: int | None = None,
    limit: int = 50,
    filters=None,
) -> PageResult:
    """游标分页：基于 id 翻页，适合大表（messages、chunks）。

    用法:
        result = await cursor_paginate(db, Message, after=last_id, limit=50)
    """
    query = model.select_active().order_by(model.id.desc())
    if filters:
        for f in filters:
            query = query.where(f)
    if after is not None:
        query = query.where(model.id < after)

    # 多查一条判断 has_more
    items = (await db.execute(query.limit(limit + 1))).scalars().all()
    has_more = len(items) > limit
    items = items[:limit]

    # 仅第一页查 total
    total = None
    if after is None:
        base = model.select_active()
        if filters:
            for f in filters:
                base = base.where(f)
        count_query = select(func.count()).select_from(base.subquery())
        total = (await db.execute(count_query)).scalar() or 0

    return PageResult(
        data=items,
        total=total or 0,
        page=1,
        page_size=limit,
    )
