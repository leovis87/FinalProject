from sqlalchemy import (
    UniqueConstraint, Column, Integer, Enum as SAEnum,
    String, Date, Boolean, DateTime, func, JSON
)
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta

from core.database import Base
from .enums import AuthProvider, UserTier, DebateResult

class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("provider", "provider_user_id", name="uq_provider_user"),
    )

    user_id = Column(Integer, primary_key=True, index=True)

    name = Column(String(50), nullable=True)
    nickname = Column(String(50), nullable=True)

    email = Column(String(255), nullable=True)
    phone_number = Column(String(20), index=True, nullable=True)
    birth_date = Column(Date, nullable=True)
    gender = Column(String(10), nullable=True)

    level = Column(Integer, default=1, nullable=False)
    exp = Column(Integer, default=0, nullable=False)
    points = Column(Integer, default=0, nullable=False)

    badges = Column(JSON, default=list, nullable=False)
    likes_received = Column(Integer, default=0, nullable=False)

    is_premium = Column(Boolean, default=False, nullable=False)

    provider = Column(
        SAEnum(AuthProvider, name="auth_provider_enum", native_enum=False),
        nullable=False,
    )
    provider_user_id = Column(String(255), nullable=False, index=True)

    refresh_token_hash = Column(String(512), nullable=True)
    refresh_token_expires_at = Column(DateTime(timezone=True), nullable=True)
    refresh_token_revoked = Column(Boolean, default=False)

    is_active = Column(Boolean, default=True, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    created_rooms = relationship("DebateRoom", back_populates="creator")
    participations = relationship("DebateParticipant", back_populates="user", cascade="all, delete-orphan")

    # 티어 필드 추가
    tier = Column(
        SAEnum(UserTier, name="user_tier_enum", native_enum=False),
        default=UserTier.ONG_AL_YI,
        nullable=False
    )
    
    level = Column(Integer, default=1, nullable=False)
    exp = Column(Integer, default=0, nullable=False)
    points = Column(Integer, default=0, nullable=False)

    @property
    def total_debates(self):
        if self.participations:
            return len(self.participations)
        return 0
    
    @property
    def win_count(self):
        if self.participations:
            return sum(1 for p in self.participations if p.result == DebateResult.WIN)
        return 0
    
    @property
    def recent_debate_count(self):
        """최근 7일 내 토론 참여 횟수"""
        if not self.participations:
            return 0
        
        limit_date = datetime.now() - timedelta(days=7)
        count = 0
        for p in self.participations:
            # timezone 정보가 있을 수 있으므로 replace로 제거 후 비교하거나 둘 다 맞춤
            if p.joined_at:
                p_date = p.joined_at.replace(tzinfo=None)
                if p_date >= limit_date:
                    count += 1
        return count