from sqlalchemy import (Column, Integer, String,
                        DateTime, Boolean,
                        ForeignKey, UniqueConstraint)
from sqlalchemy.orm import relationship
from utils.database import Base
from datetime import datetime, timezone

class DebateRooms(Base):
    __tablename__= "debate_rooms"

    id = Column(Integer, primary_key = True, autoincrement = True)
    title = Column(String, nullable = True)               # 방 제목
    topic = Column(String, nullable = False)              # 토론 주제
    room_type = Column(String, nullable = False)          # 학생 / 비즈니스 / 일반
    status = Column(String, default = "대기 중")          # 대기 중 / 진행 중 / 종료
    max_participants = Column(Integer, default = 4)       # 최대 인원 수
    current_participants = Column(Integer, default = 0)   # 현재 인원 수
    created_by = Column(String)                           # 방 개설 자 (방장)
    created_at = Column(DateTime, default = lambda: datetime.now(timezone.utc))

    # 관계 설정 (참가자, 메시지)
    participants = relationship("Participant", back_populates = "debate_rooms")
    messages = relationship("Message", back_populates = "debate_rooms")


class Participant(Base):
    __tablename__ = "participants"

    id = Column(Integer, primary_key = True, autoincrement = True)
    user_id = Column(String, nullable = False)            # 사용자 id
    nickname = Column(String, nullable = False)           # 표시될 이름
    side = Column(String)                                 # 찬성 / 반대
    is_online = Column(Boolean, default = True)
    joined_at = Column(DateTime, default = lambda: datetime.now(timezone.utc))

    # ForeignKey 설정
    room_id = Column(Integer, ForeignKey("debate_rooms.id"))

    # 관계 설정 (토론 방)
    debate_rooms = relationship("DebateRooms", back_populates = "participants")

    # 중복 방지
    __table_args__ = (
        UniqueConstraint('room_id', 'user_id', name = 'unique_room_user'),
    )


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key = True, index = True, autoincrement = True)
    sender_type = Column(String)                    # user / ai_moderator
    sender_id = Column(String)
    side = Column(String, nullable = True)          # 찬성 / 반대 / Null
    content = Column(String)
    turn_number = Column(Integer, nullable = True)
    # ⚠️ default는 인자가 없는 함수여야 함
    timestamp = Column(DateTime, default = lambda: datetime.now(timezone.utc))

    # ForeignKey 설정
    room_id = Column(Integer, ForeignKey("debate_rooms.id"))

    # 관계 설정 (토론 방)
    debate_rooms = relationship("DebateRooms", back_populates = "messages")

class User(Base):
    """
    사용자 테이블
    - 회원가입 시 생성
    - 로그인 시 검증
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, unique=True, index=True, nullable=False)   # 로그인 ID (고유)
    email = Column(String, unique=True, index=True, nullable=False)     # 이메일 (고유)
    nickname = Column(String, nullable=False)                           # 닉네임
    hashed_password = Column(String, nullable=False)                    # 암호화된 비밀번호
    is_active = Column(Boolean, default=True)                           # 계정 활성화 여부
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
