from typing import NoReturn  # ← 추가

from fastapi import HTTPException, status


def not_found(detail: str = "Not found") -> NoReturn:  # ← 반환 타입 명시
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


def conflict(detail: str = "Conflict") -> NoReturn:  # (권장) 같이 명시
    raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=detail)


def forbidden(detail: str = "Forbidden") -> NoReturn:  # (권장) 같이 명시
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=detail)
