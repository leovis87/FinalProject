from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional
from datetime import datetime

from models.enums import DebateCategory, DebateLevel, DebateStatus

class DebateRoomCreate(BaseModel):
    title: str = Field(..., max_length=100, description="토론방 제목")
    category: DebateCategory = Field(..., description="토론 주제 카테고리")
    topic: str = Field(..., max_length=200, description="토론 주제")
    topic_description: str = Field(..., min_length=5, description="주제 설명")
    level: DebateLevel = Field(DebateLevel.ALL, description="토론 난이도/학년")
    
    is_private: bool = Field(False, description="비공개 여부")
    room_password: Optional[str] = Field(None, max_length=100, description="비공개 방 비밀번호")
    allow_observers: bool = Field(True, description="관전 허용 여부")
    
    max_users: int = Field(2, ge=2, le=6, description="최대 참여 인원")
    max_turns: int = Field(4, ge=4, le=20, description="총 라운드 수")

    @model_validator(mode='after')
    def check_password_logic(self):
        is_private = self.is_private
        room_password = self.room_password

        if is_private and not room_password:
            raise ValueError('비공개 방은 비밀번호 설정이 필수입니다.')
        
        if not is_private and room_password:
            self.room_password = None
            
        return self

class DebateRoomResponse(BaseModel):
    debate_room_id: int
    creator_id: int
    title: str
    category: DebateCategory
    topic: str
    topic_description: str
    level: DebateLevel
    is_private: bool
    allow_observers: bool
    max_users: int
    current_users: int = 1
    max_turns: int
    status: DebateStatus
    created_at: datetime
    
    class Config:
        from_attributes = True