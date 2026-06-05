from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class ErrorResponse(BaseModel):
    error: str
    message: str
    details: dict = {}
    request_id: str


class SuccessResponse(BaseModel):
    message: str
    data: dict = {}


class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    per_page: int
    has_next: bool
    has_prev: bool
