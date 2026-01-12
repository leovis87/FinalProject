from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from models.enums import AuthProvider

class UserBase(BaseModel):
    name: Optional[str] = None
    nickname: Optional[str] = None
    email: Optional[str] = None

class UserRead(UserBase):
    user_id: int
    provider: AuthProvider

    class Config:
        from_attributes = True

class TestLoginRequest(BaseModel):
    email: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user_info: Optional[UserRead] = None