from sqlalchemy import Column, Integer, ForeignKey, Enum as SAEnum, DateTime, func, UniqueConstraint, Text
from sqlalchemy.orm import relationship
from core.database import Base
from .enums import DebateRole, DebateResult, DebateDecisionBy

class DebateParticipant(Base):
    __tablename__ = "debate_participants"

    debate_room_id = Column(Integer, ForeignKey("debate_rooms.debate_room_id", ondelete="CASCADE"), primary_key=True)
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), primary_key=True)

    role = Column(
        SAEnum(DebateRole, name="debate_role_enum", native_enum=False),
        nullable=False
    )

    turn_order = Column(Integer, nullable=True) 

    result = Column(
        SAEnum(DebateResult, name="debate_result_enum", native_enum=False),
        nullable=True
    )
    result_reason = Column(Text, nullable=True)
    result_decided_at = Column(DateTime(timezone=True), nullable=True)
    result_decided_by = Column(
        SAEnum(DebateDecisionBy, name="debate_decision_by_enum", native_enum=False),
        nullable=True
    )

    joined_at = Column(DateTime(timezone=True), server_default=func.now())

    debate_room = relationship("DebateRoom", back_populates="participants")
    user = relationship("User", back_populates="participations")

    __table_args__ = (
        UniqueConstraint('debate_room_id', 'role', 'turn_order', name='uq_room_role_order'),
    )

    @property
    def nickname(self):
        return self.user.nickname if self.user else "알 수 없음"
