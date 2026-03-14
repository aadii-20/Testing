"""
MongoDB document shape definitions.

Instead of SQLAlchemy ORM classes, we use plain TypedDicts
to document the expected shape of each MongoDB collection document.
These are NOT models you instantiate — they are just type hints
to make the code readable and IDE-friendly.
"""
from datetime import datetime
from typing import Optional
from typing_extensions import TypedDict


class UserDoc(TypedDict, total=False):
    """Shape of a document in the 'users' collection."""
    _id: object           # MongoDB ObjectId (auto-generated)
    email: str
    hashed_password: str
    role: str             # "student" or "teacher"
    standard: Optional[str]  # e.g. "8", "9", "10" — required for students


class ChatSessionDoc(TypedDict, total=False):
    """Shape of a document in the 'chat_sessions' collection."""
    _id: object           # MongoDB ObjectId
    user_id: str          # str(user ObjectId)
    title: Optional[str]
    subject: str
    chapter: str
    standard: Optional[str]
    language: str         # default "English"
    created_at: datetime


class ChatMessageDoc(TypedDict, total=False):
    """Shape of a document in the 'chat_messages' collection."""
    _id: object           # MongoDB ObjectId
    session_id: str       # str(session ObjectId)
    role: str             # "user" or "assistant"
    content: str
    created_at: datetime
