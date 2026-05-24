from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from hify.auth.schemas import LoginRequest, LoginResponse, UserInfo
from hify.auth.service import authenticate, get_user_by_id
from hify.core.database import get_db
from hify.core.security import get_current_user
from hify.shared.schemas import Result

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/login", response_model=Result[LoginResponse])
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    data = await authenticate(db, body.username, body.password)
    return Result.ok(data=data)


@router.get("/me", response_model=Result[UserInfo])
async def me(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    data = await get_user_by_id(db, current_user["id"])
    return Result.ok(data=data)
