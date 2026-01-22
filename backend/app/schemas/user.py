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
    level: int
    exp: int
    points: int
    badges: List[BadgeSchema] = []
    likes_received: int

    class Config:
        from_attributes = True

class TestLoginRequest(BaseModel):
    email: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user_info: Optional[UserRead] = None


class UserRead(UserBase):
    user_id: int
    provider: AuthProvider
    is_premium: bool
    tier: UserTier  # 티어 정보 추가
    level: int
    exp: int
    points: int
    badges: List[BadgeSchema] = []
    likes_received: int

    class Config:
        from_attributes = True