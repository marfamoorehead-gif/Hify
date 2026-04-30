from typing import Generic

from pydantic import BaseModel, Field

from hify.shared.types import T


class Result(BaseModel, Generic[T]):
    """统一响应格式。"""

    code: int = 200
    message: str = "success"
    data: T | None = None


class PageResult(BaseModel, Generic[T]):
    """分页响应格式。"""

    code: int = 200
    message: str = "success"
    data: list[T] = Field(default_factory=list)
    total: int = 0
    page: int = 1
    page_size: int = 20


class PageRequest(BaseModel):
    """分页请求参数。"""

    page: int = Field(default=1, ge=1, description="页码，从 1 开始")
    page_size: int = Field(default=20, ge=1, le=100, description="每页条数，最大 100")
