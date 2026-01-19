from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional, List
from datetime import datetime

from models.enums import DebateCategory, DebateLevel, DebateStatus, DebateRole, DebateResult, DebateDecisionBy

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

    creator_role: DebateRole = Field(..., description="개설자의 역할 (PRO/CON/OBSERVER)")

    @model_validator(mode='after')
    def check_password_logic(self):
        is_private = self.is_private
        room_password = self.room_password

        if is_private and not room_password:
            raise ValueError('비공개 방은 비밀번호 설정이 필수입니다.')
        
        if not is_private and room_password:
            self.room_password = None
            
        return self
    
class DebateParticipantResponse(BaseModel):
    user_id: int
    role: DebateRole
    turn_order: Optional[int] = None
    nickname: str | None = None

    class Config:
        from_attributes = True

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

    participants: List[DebateParticipantResponse] = []
    
    class Config:
        from_attributes = True

class RandomMatchRequest(BaseModel):
    level: DebateLevel = Field(DebateLevel.ALL, description="학년/난이도")
    category: DebateCategory | None = Field(None, description="과목 카테고리")
    max_users: int = Field(4, ge=2, le=6, description="최대 참여 인원")
    max_turns: int = Field(4, ge=4, le=20, description="총 라운드 수")

    @field_validator("category", mode="before")
    def normalize_category(cls, value):
        if value in (None, "", "all"):
            return None
        return value

    @field_validator("level", mode="before")
    def normalize_level(cls, value):
        if value in (None, "", "all"):
            return DebateLevel.ALL
        return value

class RandomMatchResponse(BaseModel):
    room_id: int
    room: DebateRoomResponse
    joined_role: DebateRole
    matched_existing: bool
    queued: bool

class DebateHistoryItem(BaseModel):
    debate_room_id: int
    title: str
    topic: str
    category: DebateCategory
    level: DebateLevel
    status: DebateStatus
    role: DebateRole
    result: DebateResult | None = None
    result_reason: Optional[str] = None
    joined_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None

class DebateResultItem(BaseModel):
    user_id: int
    result: DebateResult

class DebateResultUpsertRequest(BaseModel):
    results: List[DebateResultItem]
    result_reason: Optional[str] = None
    decided_by: DebateDecisionBy = DebateDecisionBy.AI

class DebateResultUpsertResponse(BaseModel):
    debate_room_id: int
    decided_at: datetime
    decided_by: DebateDecisionBy
