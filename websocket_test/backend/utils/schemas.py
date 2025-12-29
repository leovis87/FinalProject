from pydantic import BaseModel, EmailStr
from typing import (List, Dict, Tuple,
                    Union, Optional, Generator,
                    Literal)
from enum import Enum
from datetime import datetime

# Enum 설정
class SenderType(str, Enum):
    user = "user"
    ai_moderator = "ai_moderator"
    system = "system"


# Request 모델
class ChatRequest(BaseModel):
    message: str
    model: Optional[str] = "haiku"

class SystemPromptRequest(BaseModel):
    system_prompt: str

class JoinRoomRequest(BaseModel):
    side: Literal["찬성", "반대", "참관"]


# Response 모델
class RoomResponse(BaseModel):
    id: int     # 방 식별
    title: str  # 방 제목
    topic: str  # 토론 주제
    room_type: Literal["학생", "비즈니스", "일반"]
    status: Literal["대기 중", "진행 중", "종료"]
    max_participants: int  # 최대 인원 수
    current_participants: int
    created_by: str  # 방장 정보
    created_at: datetime  # 생성 시간 정보


# Create 모델
class CreateRoomRequest(BaseModel):
    title: str      # 방 제목
    topic: str      # 토론 주제
    room_type: Literal["학생", "비즈니스", "일반"]
    max_participants: int


# Login 관련
class UserRegister(BaseModel):
    """회원가입 요청"""
    user_id: str        # 로그인 ID (예: user123)
    email: EmailStr     # 이메일
    nickname: str       # 닉네임
    password: str       # 비밀번호 (평문)

    # 필요 시 활성화
    # @field_validator('password')
    # @classmethod
    # def validate_password(cls, v):
    #     """비밀번호 길이 검증"""
    #     if len(v) < 6:
    #         raise ValueError('비밀번호는 6자 이상이어야 합니다')
    #     if len(v) > 50:
    #         raise ValueError('비밀번호는 50자 이내로 입력하세요')
    #     byte_length = len(v.encode('utf-8'))
    #     if byte_length > 72:
    #         raise ValueError('비밀번호가 너무 깁니다 (72바이트 초과)')
    #     return v

class UserLogin(BaseModel):
    """로그인 요청"""
    user_id: str        # 로그인 ID
    password: str       # 비밀번호

class Token(BaseModel):
    """JWT 토큰 응답"""
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    """토큰 내부 데이터"""
    user_id: Optional[str] = None

class UserResponse(BaseModel):
    """사용자 정보 응답 (비밀번호 제외)"""
    id: int
    user_id: str
    email: str
    nickname: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True  # Pydantic v2