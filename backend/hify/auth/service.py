from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from hify.auth.models import User
from hify.auth.schemas import LoginResponse, UserInfo
from hify.core.exceptions import BizException, ErrorCode
from hify.core.security import create_access_token, verify_password


async def authenticate(
    db: AsyncSession, username: str, password: str
) -> LoginResponse:
    stmt = select(User).where(User.username == username, User.deleted == 0)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if user is None or not verify_password(password, user.password_hash):
        raise BizException(ErrorCode.UNAUTHORIZED, "用户名或密码错误")

    token = create_access_token(user.id, user.username)
    return LoginResponse(
        token=token,
        user=UserInfo(
            id=user.id,
            username=user.username,
            display_name=user.display_name,
            role=user.role,
        ),
    )


async def get_user_by_id(db: AsyncSession, user_id: int) -> UserInfo:
    stmt = select(User).where(User.id == user_id, User.deleted == 0)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if user is None:
        raise BizException(ErrorCode.UNAUTHORIZED, "用户不存在")

    return UserInfo(
        id=user.id,
        username=user.username,
        display_name=user.display_name,
        role=user.role,
    )
