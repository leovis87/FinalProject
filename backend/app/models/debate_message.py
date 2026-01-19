from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import relationship

from core.database import Base


class DebateMessage(Base):
    __tablename__ = "debate_messages"

    message_id = Column(Integer, primary_key=True, index=True)
    debate_room_id = Column(Integer, ForeignKey("debate_rooms.debate_room_id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=True, index=True)
    role = Column(String(20), nullable=False)
    display_type = Column(String(50), nullable=True)
    content = Column(Text, nullable=False)
    turn = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    debate_room = relationship("DebateRoom", backref="messages")
    user = relationship("User", backref="messages")
