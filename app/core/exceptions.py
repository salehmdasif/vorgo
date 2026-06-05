from pydantic import BaseModel


class AppError(Exception):
    """
    সব business logic error এই class থেকে raise হবে।
    HTTP status code আর machine-readable error code একসাথে carry করে।

    raise Errors.NOT_FOUND("User")
    raise Errors.UNAUTHORIZED()
    """

    def __init__(
        self,
        code: str,
        message: str,
        status_code: int,
        details: dict | None = None,
    ):
        self.code = code          # frontend এ switch করার জন্য
        self.message = message    # user কে দেখানোর জন্য
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)


class ErrorResponse(BaseModel):
    # সব error response এই format এ যাবে — frontend consistent handling করতে পারবে
    error: str        # "UNAUTHORIZED", "NOT_FOUND", etc.
    message: str      # human-readable
    details: dict     # field-level errors, extra info
    request_id: str   # log থেকে trace করার জন্য


# ── Pre-defined errors ────────────────────────────────────────────────────────
# lambda use করা হয়েছে — প্রতিটা call এ নতুন instance তৈরি হয়
# class attribute হিসেবে রাখলে একই object সব জায়গায় shared হতো
class Errors:
    UNAUTHORIZED = lambda: AppError(
        code="UNAUTHORIZED",
        message="Authentication required.",
        status_code=401,
    )
    FORBIDDEN = lambda: AppError(
        code="FORBIDDEN",
        message="You don't have permission to perform this action.",
        status_code=403,
    )
    # resource name pass করা যায়: Errors.NOT_FOUND("Invoice")
    NOT_FOUND = lambda resource="Resource": AppError(
        code="NOT_FOUND",
        message=f"{resource} not found.",
        status_code=404,
    )
    PLAN_LIMIT_EXCEEDED = lambda: AppError(
        code="PLAN_LIMIT_EXCEEDED",
        message="You have reached your plan limit. Please upgrade.",
        status_code=402,
    )
    INVALID_2FA_CODE = lambda: AppError(
        code="INVALID_2FA_CODE",
        message="Invalid or expired 2FA code.",
        status_code=400,
    )
    # WARNING: এটা raise হলে ওই user এর সব refresh token revoke হবে
    # token reuse মানে leak হয়েছে — সব session বন্ধ করাই সঠিক
    TOKEN_REUSE_DETECTED = lambda: AppError(
        code="TOKEN_REUSE_DETECTED",
        message="Security violation detected. All sessions have been revoked.",
        status_code=401,
    )
    VALIDATION_ERROR = lambda details=None: AppError(
        code="VALIDATION_ERROR",
        message="Input validation failed.",
        status_code=422,
        details=details or {},
    )
    INTERNAL_ERROR = lambda: AppError(
        code="INTERNAL_ERROR",
        message="An unexpected error occurred.",
        status_code=500,
    )
