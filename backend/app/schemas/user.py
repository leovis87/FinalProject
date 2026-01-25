from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from models.enums import AuthProvider, UserTier

class BadgeSchema(BaseModel):
    name: str
    acquired_at: datetime

class UserBase(BaseModel):
    name: Optional[str] = None
    nickname: Optional[str] = None
    email: Optional[str] = None

class UserRead(UserBase):
    user_id: int
    provider: AuthProvider
    is_premium: bool
    tier: UserTier
    level: int
    exp: int
    points: int
    badges: List[BadgeSchema] = []
    likes_received: int
    total_debates: int = 0
    win_count: int = 0
    recent_debate_count: int = 0

    class Config:
        from_attributes = True

class TestLoginRequest(BaseModel):
    email: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user_info: Optional[UserRead] = None