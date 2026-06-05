from pydantic import BaseModel


class AppError(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        status_code: int,
        details: dict | None = None,
    ):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)


class ErrorResponse(BaseModel):
    error: str
    message: str
    details: dict
    request_id: str


class Errors:
    @staticmethod
    def UNAUTHORIZED() -> AppError:
        return AppError(
            code="UNAUTHORIZED", message="Authentication required.", status_code=401
        )

    @staticmethod
    def FORBIDDEN() -> AppError:
        return AppError(
            code="FORBIDDEN",
            message="You don't have permission to perform this action.",
            status_code=403,
        )

    @staticmethod
    def NOT_FOUND(resource: str = "Resource") -> AppError:
        return AppError(
            code="NOT_FOUND", message=f"{resource} not found.", status_code=404
        )

    @staticmethod
    def PLAN_LIMIT_EXCEEDED() -> AppError:
        return AppError(
            code="PLAN_LIMIT_EXCEEDED",
            message="You have reached your plan limit. Please upgrade.",
            status_code=402,
        )

    @staticmethod
    def INVALID_2FA_CODE() -> AppError:
        return AppError(
            code="INVALID_2FA_CODE",
            message="Invalid or expired 2FA code.",
            status_code=400,
        )

    @staticmethod
    def TOKEN_REUSE_DETECTED() -> AppError:
        return AppError(
            code="TOKEN_REUSE_DETECTED",
            message="Security violation detected. All sessions have been revoked.",
            status_code=401,
        )

    @staticmethod
    def VALIDATION_ERROR(details: dict | None = None) -> AppError:
        return AppError(
            code="VALIDATION_ERROR",
            message="Input validation failed.",
            status_code=422,
            details=details or {},
        )

    @staticmethod
    def ACCOUNT_LOCKED() -> AppError:
        return AppError(
            code="ACCOUNT_LOCKED",
            message="Too many failed attempts. Try again in 15 minutes.",
            status_code=429,
        )

    @staticmethod
    def RATE_LIMITED() -> AppError:
        return AppError(
            code="RATE_LIMITED",
            message="Too many requests. Slow down.",
            status_code=429,
        )

    @staticmethod
    def INTERNAL_ERROR() -> AppError:
        return AppError(
            code="INTERNAL_ERROR",
            message="An unexpected error occurred.",
            status_code=500,
        )
