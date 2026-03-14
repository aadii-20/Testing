from typing import List

from fastapi import Depends, HTTPException, status

from auth.auth import get_current_user
from auth.schemas import UserRead


def role_required(*required_roles: str):
    """
    FastAPI dependency to enforce that the current user has
    one of the allowed roles. Returns the current user.
    """
    allowed: List[str] = list(required_roles)

    def checker(user: UserRead = Depends(get_current_user)) -> UserRead:
        if allowed and user.role not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied for this role",
            )
        return user

    return checker
