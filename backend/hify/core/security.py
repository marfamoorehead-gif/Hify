from datetime import datetime, timedelta, timezone

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

from hify.core.config import settings
from hify.core.exceptions import BizException, ErrorCode

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
bearer_scheme = HTTPBearer()


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(user_id: int, username: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    payload = {"sub": str(user_id), "username": username, "exp": expire}
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    try:
        return jwt.decode(
            token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
        )
    except jwt.ExpiredSignatureError:
        raise BizException(ErrorCode.TOKEN_EXPIRED)
    except JWTError:
        raise BizException(ErrorCode.UNAUTHORIZED)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> dict:
    """解析 Bearer token，返回 {"id": user_id, "username": str}。

    V1 简单实现：直接从 token payload 读取用户信息。
    V2 如需实时校验用户状态，可在此查数据库。
    """
    payload = decode_access_token(credentials.credentials)
    return {"id": int(payload["sub"]), "username": payload["username"]}
