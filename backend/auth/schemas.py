from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime


class UserBase(BaseModel):
    email: EmailStr


class UserCreate(UserBase):
    password: str
    role: str  # "student" or "teacher"
    standard: Optional[str] = None


class UserRead(UserBase):
    id: str        # MongoDB ObjectId as string
    role: str
    standard: Optional[str] = None

    model_config = {"from_attributes": False}


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginResponse(BaseModel):
    token: str
    role: str


class TokenData(BaseModel):
    email: Optional[EmailStr] = None
    role: Optional[str] = None
    standard: Optional[str] = None


# --- Chat Schemas ---

class ChatRequest(BaseModel):
    subject: str
    chapter: str
    question: str
    language: Optional[str] = "English"


class ChatResponse(BaseModel):
    answer: str


class Subject(BaseModel):
    name: str
    chapters: List[str]


# --- Chat History Schemas ---

class ChatMessageBase(BaseModel):
    role: str
    content: str


class ChatMessageCreate(ChatMessageBase):
    pass


class ChatMessageRead(ChatMessageBase):
    id: str         # MongoDB ObjectId as string
    session_id: str  # MongoDB ObjectId as string
    created_at: datetime

    model_config = {"from_attributes": False}


class ChatSessionBase(BaseModel):
    subject: str
    chapter: str
    standard: Optional[str] = None
    language: str = "English"
    title: Optional[str] = None


class ChatSessionCreate(ChatSessionBase):
    pass


class ChatSessionRead(ChatSessionBase):
    id: str          # MongoDB ObjectId as string
    user_id: str     # MongoDB ObjectId as string
    created_at: datetime
    messages: List[ChatMessageRead] = []

    model_config = {"from_attributes": False}
