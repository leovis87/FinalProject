from sqlalchemy import (
    Column, Integer, String, Text, ForeignKey, DateTime,
    Boolean, Enum as SAEnum, func
)
from sqlalchemy.orm import relationship

from core.database import Base
from .enums import DebateLevel, DebateStatus

class DebateRoom(Base):
    __tablename__ = "debate_rooms"

    debate_room_id = Column(Integer, primary_key=True, index=True)

    creator_id = Column(Integer, ForeignKey("users.user_id", nullable=False))

    title = Column(String(100), nullable=False)
    category = Column(String, nullable=False) # categroy 테이블
    topic = Column(String(100), nullable=False) # topic 테이블
    topic_description = Column(Text, nullable=True)

    level = Column(
        SAEnum(DebateLevel, name="debate_level_enum", native_enum=False),
        default=DebateLevel.ALL,
        nullable=False
    )

    max_users = Column(Integer, default=2)
    max_turns = Column(Integer, default=4)

    status = Column(
        SAEnum(DebateStatus, name="debate_status_enum", native_enum=False),
        default=DebateStatus.WAITING,
        nullable=False
    )

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    started_at = Column(DateTime(timezone=True), nullable=True)
    finished_at = Column(DateTime(timezone=True), nullable=True)

    creator = relationship("User", back_populates="created_rooms")