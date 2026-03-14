from datetime import datetime, timedelta
import os
from typing import Optional

import bcrypt
from bson import ObjectId
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from pymongo.database import Database

from database import get_db
from auth import schemas

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

SECRET_KEY = os.getenv("SECRET_KEY", "CHANGE_ME_IN_PRODUCTION")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))


def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def authenticate_user(email: str, password: str) -> Optional[dict]:
    """
    Look up user by email in MongoDB and verify password.
    Returns the user document (dict) or None.
    """
    db = get_db()
    user = db["users"].find_one({"email": email})
    if not user:
        return None
    if not verify_password(password, user["hashed_password"]):
        return None
    return user


def _user_doc_to_schema(user: dict) -> schemas.UserRead:
    """Convert a MongoDB user document to a UserRead Pydantic model."""
    return schemas.UserRead(
        id=str(user["_id"]),
        email=user["email"],
        role=user["role"],
        standard=user.get("standard"),
    )


def get_current_user(
    token: str = Depends(oauth2_scheme),
) -> schemas.UserRead:
    """
    FastAPI dependency: validates the JWT and returns the current user.
    Fetches the user record from MongoDB to ensure the account still exists.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        role: str = payload.get("role")
        if email is None or role is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    db = get_db()
    user = db["users"].find_one({"email": email})
    if user is None:
        raise credentials_exception

    return _user_doc_to_schema(user)
