from sqlalchemy import (
    Column, Integer, String, Text, ForeignKey, DateTime,
    Boolean, Enum as SAEnum, func
)
from sqlalchemy.orm import relationship

from core.database import Base
from .enums import DebateLevel, DebateStatus, DebateCategory

class DebateRoom(Base):
    __tablename__ = "debate_rooms"

    debate_room_id = Column(Integer, primary_key=True, index=True)

    creator_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)

    title = Column(String(100), nullable=False)
    
    # 카테고리
    category = Column(
        SAEnum(DebateCategory, name="debate_category_enum", native_enum=False),
        nullable=False
    )
    
    topic = Column(String(200), nullable=False)
    topic_description = Column(Text, nullable=False)

    # 학년/난이도
    level = Column(
        SAEnum(DebateLevel, name="debate_level_enum", native_enum=False),
        default=DebateLevel.ALL,
        nullable=False
    )

    # 방 설정
    is_private = Column(Boolean, default=False, nullable=False) # 공개/비공개
    room_password = Column(String(100), nullable=True) # 비공개 시 비밀번호
    allow_observers = Column(Boolean, default=True, nullable=False) # 관전 허용 여부

    max_users = Column(Integer, default=2) # 1:1 or 2:2 등
    
    # 토론 규칙
    max_turns = Column(Integer, default=4) # 라운드 수 (예: 입론, 반론, 재반론, 결론 = 4)

    status = Column(
        SAEnum(DebateStatus, name="debate_status_enum", native_enum=False),
        default=DebateStatus.WAITING,
        nullable=False
    )

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    started_at = Column(DateTime(timezone=True), nullable=True)
    finished_at = Column(DateTime(timezone=True), nullable=True)

    creator = relationship("User", back_populates="created_rooms")