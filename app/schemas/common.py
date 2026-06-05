from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class ErrorResponse(BaseModel):
    # main.py এর exception handler এখান থেকে serialize করে পাঠায়
    # frontend এ `error` field দিয়ে switch করো, `message` user কে দেখাও
    error: str
    message: str
    details: dict = {}
    request_id: str


class SuccessResponse(BaseModel):
    # simple confirmation response এর জন্য - delete, update, etc.
    message: str
    data: dict = {}


class PaginatedResponse(BaseModel, Generic[T]):
    # cursor-based pagination এ নয়, offset-based এ use করো
    # large dataset এ cursor-based prefer করো - commit 6 এ TenantService এ implement হবে
    items: list[T]
    total: int
    page: int
    per_page: int
    has_next: bool
    has_prev: bool
